pipeline {
    agent any

    environment {
        VENV = "venv"
        PYTHON = "python"   // portable → uses whichever python is in PATH
        STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false"

        // Non-sensitive values
        JENKINS_URL = "Your_Jenkins_URL" // e.g., https://your-jenkins-instance.com
        JOB_NAME = "Your_Job_Name"   // e.g., "example-job"
    }

    stages {
        stage('Setup Python') {
            steps {
                script {
                    if (isUnix()) {
                        sh """
                            ${PYTHON} -m venv ${VENV}
                            . ${VENV}/bin/activate
                            pip install --upgrade pip
                            pip install -r requirements.txt
                        """
                    } else {
                        bat """
                            %PYTHON% -m venv %VENV%
                            %VENV%\\Scripts\\python.exe -m pip install --upgrade pip
                            %VENV%\\Scripts\\python.exe -m pip install -r requirements.txt
                        """
                    }
                }
            }
        }

    stage('Simulate Python Import Error') {
        steps {
            bat """
                %VENV%\\Scripts\\python.exe -c "import non_existing_module"
            """
        }
    }

        stage('Run Application (Web Mode)') {
            when {
                expression { return false } // Disabled in Jenkins
            }
            steps {
                withCredentials([
                    string(credentialsId: 'PINECONE_API_KEY', variable: 'PINECONE_API_KEY'),
                    string(credentialsId: 'GEMINI_API_KEY', variable: 'GEMINI_API_KEY'),
                    string(credentialsId: 'JENKINS_USER', variable: 'JENKINS_USER'),
                    string(credentialsId: 'JENKINS_API_TOKEN', variable: 'JENKINS_API_TOKEN')
                ]) {
                    script {
                        if (isUnix()) {
                            sh """
                                export PINECONE_API_KEY=${PINECONE_API_KEY}
                                export GEMINI_API_KEY=${GEMINI_API_KEY}
                                export JENKINS_URL=${JENKINS_URL}
                                export JOB_NAME=${JOB_NAME}
                                export JENKINS_USER=${JENKINS_USER}
                                export JENKINS_API_TOKEN=${JENKINS_API_TOKEN}
                                export MODE=web
                                . ${VENV}/bin/activate
                                streamlit run app.py --server.port 8501 --server.headless true
                            """
                        } else {
                            bat """
                                set PINECONE_API_KEY=%PINECONE_API_KEY%
                                set GEMINI_API_KEY=%GEMINI_API_KEY%
                                set JENKINS_URL=%JENKINS_URL%
                                set JOB_NAME=%JOB_NAME%
                                set JENKINS_USER=%JENKINS_USER%
                                set JENKINS_API_TOKEN=%JENKINS_API_TOKEN%
                                set MODE=web
                                %VENV%\\Scripts\\streamlit run app.py --server.port 8501 --server.headless true
                            """
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline finished (success or failure)."
        }
        success {
            echo "Build succeeded."
        }
        failure {
            echo "Build failed. Running CLI error resolver..."

            withCredentials([
                string(credentialsId: 'PINECONE_API_KEY', variable: 'PINECONE_API_KEY'),
                string(credentialsId: 'GEMINI_API_KEY', variable: 'GEMINI_API_KEY'),
                string(credentialsId: 'JENKINS_USER', variable: 'JENKINS_USER'),
                string(credentialsId: 'JENKINS_API_TOKEN', variable: 'JENKINS_API_TOKEN')
            ]) {
                script {
                    if (isUnix()) {
                        sh """
                            export PINECONE_API_KEY=${PINECONE_API_KEY}
                            export GEMINI_API_KEY=${GEMINI_API_KEY}
                            export JENKINS_URL=${JENKINS_URL}
                            export JOB_NAME=${JOB_NAME}
                            export JENKINS_USER=${JENKINS_USER}
                            export JENKINS_API_TOKEN=${JENKINS_API_TOKEN}
                            export MODE=cli
                            . ${VENV}/bin/activate
                            python app.py
                        """
                    } else {
                        bat """
                            set PINECONE_API_KEY=%PINECONE_API_KEY%
                            set GEMINI_API_KEY=%GEMINI_API_KEY%
                            set JENKINS_URL=%JENKINS_URL%
                            set JOB_NAME=%JOB_NAME%
                            set JENKINS_USER=%JENKINS_USER%
                            set JENKINS_API_TOKEN=%JENKINS_API_TOKEN%
                            set MODE=cli
                            %VENV%\\Scripts\\python.exe app.py
                        """
                    }
                }
            }
        }
    }
}
