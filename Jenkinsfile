pipeline {
    agent any

    environment {
        VENV = ".venv"
        GEMINI_API_KEY = credentials('GEMINI_API_KEY')
        PINECONE_API_KEY = credentials('PINECONE_API_KEY')
    }

    stages {
        stage('Checkout') {
            steps {
                echo "📥 Checking out source code..."
                checkout scm
            }
        }

        stage('Setup Python') {
            steps {
                echo "🐍 Setting up Python environment..."
                sh """
                    rm -rf ${VENV}
                    python3 -m venv ${VENV}
                    . ${VENV}/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                """
            }
        }

        stage('Run Application') {
            steps {
                echo "▶ Running your app..."
                sh """
                    . ${VENV}/bin/activate
                    python3 app.py
                """
            }
        }
    }

    post {
        always {
            echo "🧹 Cleaning up..."
            sh "rm -rf ${VENV}"
        }
        success {
            echo "✅ Pipeline completed successfully!"
        }
        failure {
            echo "❌ Pipeline failed. Check logs."
        }
    }
}
