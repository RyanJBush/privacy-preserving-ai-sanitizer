"""Candidate detector: Presidio rule-based recognizers on a spaCy NLP engine.

NOT a trained PII model. Three rule-based recognizers are registered (email, US phone, a
custom CUSTOMER_ID regex); the small spaCy model only provides tokens/lemmas for Presidio's
context enhancer and no NER recognizer is registered. Requires presidio-analyzer and the
en_core_web_sm model. sanitizer.core never imports this module, so the stdlib-only baseline
is unaffected.
"""
import logging
from typing import Any, Callable, Dict, List

import regex
import tldextract
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.predefined_recognizers import EmailRecognizer, PhoneRecognizer

from .core import ENTITY_PRIORITY

LANGUAGE = "en"
SPACY_MODEL = "en_core_web_sm"
PHONE_REGIONS = ("US",)  # frozen scope: US only; the shared exact-format gate narrows it further

# Same rule as the baseline: case-sensitive CUST- + exactly six ASCII digits, not inside a token.
CUSTOMER_ID_REGEX = r"(?<![A-Za-z0-9_])CUST-[0-9]{6}(?![A-Za-z0-9_])"

# Stock EmailRecognizer.validate_result calls tldextract.extract(), whose default extractor
# tries to download the Public Suffix List (publicsuffix.org, then raw.githubusercontent.com)
# and writes a cache inside site-packages or the user profile. This subclass validates with
# the suffix snapshot bundled in the tldextract wheel: no network, no cache directory. The
# snapshot can be stale versus the live list. (The stock recognizer is reachable only through
# the diagnostic `python -m sanitizer.presidio_check --stock-email`, never through the CLI.)
_OFFLINE_TLD = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)


class OfflineEmailRecognizer(EmailRecognizer):
    def validate_result(self, pattern_text: str):
        return _OFFLINE_TLD(pattern_text).fqdn != ""


def build_registry(stock_email: bool = False) -> RecognizerRegistry:
    registry = RecognizerRegistry(supported_languages=[LANGUAGE])
    email_cls = EmailRecognizer if stock_email else OfflineEmailRecognizer
    registry.add_recognizer(email_cls(supported_language=LANGUAGE))
    registry.add_recognizer(PhoneRecognizer(supported_language=LANGUAGE, supported_regions=PHONE_REGIONS))
    registry.add_recognizer(PatternRecognizer(
        supported_entity="CUSTOMER_ID",
        name="CustomerIdRecognizer",
        supported_language=LANGUAGE,
        patterns=[Pattern("customer-id", CUSTOMER_ID_REGEX, 1.0)],
        # Presidio's default flags include IGNORECASE; the rule is case-sensitive.
        global_regex_flags=regex.MULTILINE | regex.DOTALL,
    ))
    return registry


def build_analyzer(stock_email: bool = False) -> AnalyzerEngine:
    # Presidio's DEBUG records include input text (LemmaContextAwareEnhancer logs
    # "Context list is: ... <text around the match>"). This process-wide setting keeps that
    # logger at INFO or above. It does NOT protect against an application re-lowering the level.
    logging.getLogger("presidio-analyzer").setLevel(logging.INFO)
    nlp_engine = NlpEngineProvider(nlp_configuration={
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": LANGUAGE, "model_name": SPACY_MODEL}],
    }).create_engine()
    return AnalyzerEngine(registry=build_registry(stock_email), nlp_engine=nlp_engine,
                          supported_languages=[LANGUAGE])


def make_detector(analyzer: AnalyzerEngine = None) -> Callable[[str], List[Dict[str, Any]]]:
    """Return detector(text) -> raw candidates in the sanitizer's detector contract (all scores)."""
    analyzer = analyzer or build_analyzer()

    def detect(text: str) -> List[Dict[str, Any]]:
        results = analyzer.analyze(text=text, language=LANGUAGE, entities=list(ENTITY_PRIORITY))
        return [{"entity_type": r.entity_type, "start": r.start, "end": r.end, "score": r.score}
                for r in results]

    return detect


def recognizer_settings(analyzer: AnalyzerEngine) -> Dict[str, Any]:
    """Settings recorded in frozen_config.json (read from the live objects, not retyped)."""
    recognizers = []
    for r in analyzer.registry.recognizers:
        item = {"name": r.name, "class": type(r).__name__, "entities": list(r.supported_entities)}
        if hasattr(r, "supported_regions"):
            item["supported_regions"] = list(r.supported_regions)
            item["leniency"] = r.leniency
            item["base_score"] = r.SCORE
        if hasattr(r, "patterns"):
            item["patterns"] = [{"name": p.name, "regex": p.regex, "score": p.score} for p in r.patterns]
            item["regex_flags"] = repr(r.global_regex_flags)
        recognizers.append(item)
    return {
        "recognizers": recognizers,
        "nlp_engine": type(analyzer.nlp_engine).__name__,
        "spacy_model": SPACY_MODEL,
        "spacy_pipeline": list(analyzer.nlp_engine.nlp[LANGUAGE].pipe_names),
        "ner_recognizer_registered": any(type(r).__name__ == "SpacyRecognizer" for r in analyzer.registry.recognizers),
        "context_enhancer": type(analyzer.context_aware_enhancer).__name__,
        "analyze_entities": list(ENTITY_PRIORITY),
        "engine_default_score_threshold": analyzer.default_score_threshold,
        "email_validator": "offline tldextract snapshot (suffix_list_urls=(), cache_dir=None)",
        "presidio_logger_level": "INFO (process-wide setting made in build_analyzer)",
    }
