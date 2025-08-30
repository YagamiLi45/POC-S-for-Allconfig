pipeline {
    agent any

    environment {
        VENV = "venv"
        PYTHON = "C:\\Users\\mtamb\\AppData\\Local\\Programs\\Python\\Python311\\python.exe"
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
                    if exist %VENV% rmdir /S /Q %VENV%
                    "%PYTHON%" -m venv %VENV%
                    call %VENV%\\Scripts\\activate
                    %VENV%\\Scripts\\pip install --upgrade pip
                    %VENV%\\Scripts\\pip install -r requirements.txt
                """
            }
        }

        stage('Run Application') {
            steps {
                echo "Running application..."
                bat """
                    %VENV%\\Scripts\\python.exe app.py
                """
            }
        }
    }

    post {
        always {
            echo "Cleaning up..."
            bat """
                if exist %VENV% rmdir /S /Q %VENV%
            """
        }
        success {
            echo "Pipeline completed successfully!"
        }
        failure {
            echo "Pipeline failed. Check logs."
        }
    }
}
