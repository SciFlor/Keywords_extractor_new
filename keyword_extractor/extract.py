from flask import Flask, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk
import string
import logging

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)


def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()

    # Remove special characters, but keep alphanumeric characters and spaces
    text = ''.join([char for char in text if char.isalnum() or char.isspace()])

    # Tokenize
    tokens = word_tokenize(text)

    # Remove stopwords
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words and len(token) > 1]

    preprocessed_text = ' '.join(tokens)
    return preprocessed_text


def extract_keywords(text, max_keywords=20):
    preprocessed_text = preprocess_text(text)

    if not preprocessed_text:
        app.logger.warning("No words left after preprocessing")
        return {}

    try:
        vectorizer = TfidfVectorizer(max_features=max_keywords)
        tfidf_matrix = vectorizer.fit_transform([preprocessed_text])

        feature_names = vectorizer.get_feature_names_out()
        tfidf_scores = tfidf_matrix.toarray()[0]

        keywords = {}
        for keyword, score in zip(feature_names, tfidf_scores):
            frequency = preprocessed_text.count(keyword)
            trust_interval = min(1.0, 0.3 + (score * 0.7))
            keywords[keyword] = {
                'frequency': frequency,
                'trust_interval': round(trust_interval, 2)
            }

        return keywords
    except ValueError as e:
        app.logger.warning(f"TfidfVectorizer failed: {str(e)}. Falling back to simple word frequency.")
        # If TfidfVectorizer fails, fall back to simple word frequency
        words = preprocessed_text.split()
        word_freq = {}
        for word in words:
            if word not in word_freq:
                word_freq[word] = 1
            else:
                word_freq[word] += 1

        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = {}
        for word, freq in sorted_words[:max_keywords]:
            keywords[word] = {
                'frequency': freq,
                'trust_interval': round(min(1.0, 0.3 + (freq / len(words))), 2)
            }

        return keywords


@app.route('/extract', methods=['POST'])
def extract():
    try:
        data = request.json

        if not data or 'text' not in data:
            return jsonify({"error": "Invalid input data"}), 400

        text = data['text']
        keywords = extract_keywords(text)

        app.logger.info(f"Processed text and extracted {len(keywords)} keywords")
        return jsonify(keywords)

    except Exception as e:
        app.logger.error(f"An error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

