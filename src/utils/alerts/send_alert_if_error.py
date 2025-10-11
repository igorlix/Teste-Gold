import requests
import json
import sys
from pyspark.sql import SparkSession

# Slack Webhook URL
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

# Function to identify the environment
def detect_environment():
    try:
        cluster_name = spark.conf.get("spark.databricks.clusterUsageTags.clusterName", "Unknown")
        if "dev" in cluster_name.lower():
            return "dev"
        elif "prd" in cluster_name.lower():
            return "prd"
        else:
            return f"unknown ({cluster_name})"
    except Exception as e:
        return f"error detecting environment ({str(e)})"

# Function to send an alert to Slack
def send_slack_alert(job_name, error_message, environment):
    message = {
        "text": f":rotating_light: *Databricks Job Failure Alert!* :rotating_light:\n\n"
                f"🌍 *Environment*: `{environment}`\n"
                f"💾 *Job*: `{job_name}`\n"
                f"❌ *Error*: `{error_message}`"
    }

    headers = {"Content-Type": "application/json"}
    response = requests.post(SLACK_WEBHOOK_URL, data=json.dumps(message), headers=headers)

    if response.status_code == 200:
        print("✅ Alert sent to Slack!")
    else:
        print(f"❌ Failed to send alert. Code: {response.status_code}, Response: {response.text}")

# Capture arguments passed by the Workflow (parameters)
try:
    job_name = dbutils.widgets.get("job_name")
    error_message = dbutils.widgets.get("error_message")
except:
    job_name = "Unknown Job Name"
    error_message = "Unidentified error."

# Detect the environment
environment = detect_environment()

# Send alert
send_slack_alert(job_name, error_message, environment)
