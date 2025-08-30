pipeline {
    agent any

    environment {
        VENV = "venv"
        GEMINI_API_KEY = credentials('GEMINI_API_KEY')
        PINECONE_API_KEY = credentials('PINECONE_API_KEY')
    }

    stages {
        stage('Checkout') {
            steps {
                echo "Checking out source code..."
                checkout scm
            }
        }

        stage('Setup Python') {
            steps {
                echo "Setting up Python environment..."
                bat """
                    rmdir /S /Q %VENV%
                    python -m venv %VENV%
                    call %VENV%\\Scripts\\activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                """
            }
        }

        stage('Run Application') {
            steps {
                echo "Running your app..."
                bat """
                    call %VENV%\\Scripts\\activate
                    python app.py
                """
            }
        }
    }

    post {
        always {
            echo "Cleaning up..."
            bat "rmdir /S /Q %VENV%"
        }
        success {
            echo "Pipeline completed successfully!"
        }
        failure {
            echo "Pipeline failed. Check logs."
        }
    }
}
