"""
Módulo de categorización de mensajes usando palabras clave y similitud fuzzy.
"""

from difflib import SequenceMatcher
from typing import Optional

from app.config import config
from app.models import Category
from app.utils import LoggerConfig, TextNormalizer, StringHelper


class MessageCategorizer:
    """
    Categorizador de mensajes usando coincidencias exactas y similitud fuzzy.
    
    Proceso de categorización:
    1. Busca coincidencias exactas con palabras clave
    2. Si no encuentra, usa difflib para similitud fuzzy
    3. Retorna la categoría con mayor confidence score
    4. Si ninguna supera el threshold, asigna categoría por defecto
    """
    
    def __init__(self, similarity_threshold: Optional[float] = None):
        self.similarity_threshold = similarity_threshold or config.similarity_threshold
        self.default_category = config.default_category
        self.logger = LoggerConfig.setup_logger(__name__)
    
    def categorize_message(self, message_text: str, categories: list[Category]) -> dict:
        if not message_text or not categories:
            return {
                'category': self.default_category,
                'confidence_score': 0.0
            }
        
        normalized_message = TextNormalizer.clean_and_normalize(message_text)
        message_words = set(StringHelper.extract_words(normalized_message))
        
        exact_match = self._find_exact_keyword_match(message_words, categories)
        if exact_match:
            return exact_match
        
        fuzzy_match = self._find_fuzzy_match(normalized_message, categories)
        if fuzzy_match:
            return fuzzy_match
        
        self.logger.debug(f"No se encontró categoría para: '{message_text[:50]}'")
        return {
            'category': self.default_category,
            'confidence_score': 0.0
        }
    
    def _find_exact_keyword_match(self, message_words: set[str], categories: list[Category]) -> Optional[dict]:
        best_match = None
        max_matches = 0
        
        for category in categories:
            normalized_keywords = [
                TextNormalizer.clean_and_normalize(kw) 
                for kw in category.keywords
            ]
            
            matches = sum(1 for keyword in normalized_keywords if keyword in message_words)
            
            if matches > max_matches:
                max_matches = matches
                total_keywords = len(normalized_keywords)
                confidence = min(matches / total_keywords, 1.0)
                
                best_match = {
                    'category': category.name,
                    'confidence_score': confidence
                }
        
        if best_match and best_match['confidence_score'] >= self.similarity_threshold:
            self.logger.info(f"Match exacto: {best_match['category']} (score: {best_match['confidence_score']:.2f})")
            return best_match
        
        return None
    
    def _find_fuzzy_match(self, normalized_message: str, categories: list[Category]) -> Optional[dict]:
        best_match = None
        max_similarity = 0.0
        
        for category in categories:
            category_text = " ".join(category.keywords)
            normalized_category_text = TextNormalizer.clean_and_normalize(category_text)
            
            similarity = self._calculate_similarity(normalized_message, normalized_category_text)
            
            if similarity > max_similarity:
                max_similarity = similarity
                best_match = {
                    'category': category.name,
                    'confidence_score': similarity
                }
        
        if best_match and best_match['confidence_score'] >= self.similarity_threshold:
            self.logger.info(f"Match fuzzy: {best_match['category']} (score: {best_match['confidence_score']:.2f})")
            return best_match
        
        return None
    
    def _calculate_similarity(self, text_a: str, text_b: str) -> float:
        if not text_a or not text_b:
            return 0.0
        
        sequence_matcher = SequenceMatcher(None, text_a, text_b)
        return sequence_matcher.ratio()
    
    def _calculate_keyword_similarity(self, message_words: set[str], keywords: list[str]) -> float:
        if not message_words or not keywords:
            return 0.0
        
        normalized_keywords = [
            TextNormalizer.clean_and_normalize(kw) 
            for kw in keywords
        ]
        
        max_similarities = []
        for message_word in message_words:
            word_similarities = [
                self._calculate_similarity(message_word, keyword)
                for keyword in normalized_keywords
            ]
            if word_similarities:
                max_similarities.append(max(word_similarities))
        
        if not max_similarities:
            return 0.0
        
        return sum(max_similarities) / len(max_similarities)
    
    def get_category_scores(self, message_text: str, categories: list[Category]) -> list[dict]:
        normalized_message = TextNormalizer.clean_and_normalize(message_text)
        message_words = set(StringHelper.extract_words(normalized_message))
        
        scores = []
        for category in categories:
            category_text = " ".join(category.keywords)
            normalized_category_text = TextNormalizer.clean_and_normalize(category_text)
            
            exact_score = len(message_words.intersection(
                set(TextNormalizer.clean_and_normalize(kw) for kw in category.keywords)
            )) / len(category.keywords) if category.keywords else 0.0
            
            fuzzy_score = self._calculate_similarity(normalized_message, normalized_category_text)
            
            final_score = max(exact_score, fuzzy_score)
            
            scores.append({
                'category': category.name,
                'score': final_score,
                'exact_matches': exact_score,
                'fuzzy_similarity': fuzzy_score
            })
        
        return sorted(scores, key=lambda x: x['score'], reverse=True)