import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from underthesea import word_tokenize
import numpy as np

logger = logging.getLogger(__name__)


class TFIDFProcessor:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            tokenizer=self._vietnamese_tokenize,
            max_features=700,
            token_pattern=None,
            ngram_range=(1, 2)
        )

    def _vietnamese_tokenize(self, text):
        try:
            return word_tokenize(text, format="text").split()
        except Exception as e:
            logger.error(f"Lỗi khi tokenize văn bản: {str(e)}")
            return text.split()

    def get_important_sentences(self, text, num_sentences=10):
        try:
            # Tách câu
            sentences = text.split('.')
            sentences = [s.strip() for s in sentences if s.strip()]

            if not sentences:
                return text

            # Tính TF-IDF cho toàn bộ văn bản
            tfidf_matrix = self.vectorizer.fit_transform([text])
            feature_names = self.vectorizer.get_feature_names_out()

            # Tính điểm cho từng câu
            sentence_scores = []
            for sentence in sentences:
                sentence_tokens = self._vietnamese_tokenize(sentence)
                score = 0
                for token in sentence_tokens:
                    if token in feature_names:
                        token_idx = np.where(feature_names == token)[0]
                        if len(token_idx) > 0:
                            score += tfidf_matrix[0, token_idx[0]]
                sentence_scores.append((sentence, score))

            # Sắp xếp câu theo điểm số
            sentence_scores.sort(key=lambda x: x[1], reverse=True)

            # Lấy top N câu quan trọng nhất
            important_sentences = [s[0]
                                   for s in sentence_scores[:num_sentences]]

            # Sắp xếp lại các câu theo thứ tự xuất hiện trong văn bản gốc
            important_sentences.sort(key=lambda x: text.find(x))

            return '. '.join(important_sentences) + '.'

        except Exception as e:
            logger.error(f"Lỗi khi xử lý TF-IDF: {str(e)}")
            return text
