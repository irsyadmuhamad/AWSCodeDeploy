import json
import os

import urllib3

http = urllib3.PoolManager()

SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]


def gen_message_from_codepipeline_event(event_dict):
    """
    Return message according to the CodePipeline state.
    """

# Message when STARTED
    if event_dict["detail"]["state"] == "STARTED":
        message = "CodePipeline state: STARTED:bulb:"

        started_stage = event_dict.get("detail", {}).get("stage")
        #started_stage = event_dict.get("actionStates", {}).get("actionName")
        #started_stage = event_dict.get("additionalAttributes", {}).get("startedStage")
        stage_info = (
            f"Started Stage: {started_stage}"
            if started_stage
            else "Started Stage: N/A"
        )
        message += f"\n{stage_info}"

        started_actions = event_dict.get("additionalAttributes", {}).get("sourceActions", {})
        if started_actions:
            # Send only the last try info
            #info_last_action = started_actions[-1]['BranchName']
            info_last_action = started_actions[-1]['sourceActionVariables']
            #info_last_action = started_actions[-1]['sourceActionProvider']
            message += f"\nInformation: {info_last_action}"

        return message

    # Message when SUCCEEDED
    if event_dict["detail"]["state"] == "SUCCEEDED":
        message = "CodePipeline state: SUCCEEDED:white_check_mark:"

        succeeded_stage = event_dict.get("detail", {}).get("stage")
        #succeeded_stage = event_dict.get("additionalAttributes", {}).get("succeededStage")
        stage_info = (
            f"Succeeded Stage: {succeeded_stage}"
            if succeeded_stage
            else "Succeeded Stage: N/A"
        )
        message += f"\n{stage_info}"

        succeeded_actions = event_dict.get("additionalAttributes", {}).get("succeededActions")
        if succeeded_actions:
            # Send only the last try info
            info_last_action = succeeded_actions[-1]['additionalInformation']
            message += f"\nInformation: {info_last_action}"

        return message

    # Message when FAILED
    if event_dict["detail"]["state"] == "FAILED":
        message = "CodePipeline state: FAILED:x:"

        failed_stage = event_dict.get("additionalAttributes", {}).get("failedStage")
        stage_info = (
            f"Failed Stage: {failed_stage}"
            if failed_stage
            else "Failed Stage: N/A"
        )
        message += f"\n{stage_info}"

        failed_actions = event_dict.get("additionalAttributes", {}).get("failedActions")
        if failed_actions:
            # Send only the last try info
            info_last_action = failed_actions[-1]['additionalInformation']
            message += f"\nInformation: {info_last_action}"

        return message


def lambda_handler(event, context):
    """
    Handle CodePipeline notifications and send messages to Slack.
    """

    try:
        event_str = event["Records"][0]["Sns"]["Message"]
    except (KeyError, IndexError):
        print("Error: Event is missing required data")
        return

    event_dict = json.loads(event_str)

    # generate message
    message = gen_message_from_codepipeline_event(event_dict)
    #if not message:
    #    print({"statusCode": 200, "body": "No message to return."})
    #    return
    region = event_dict["region"]
    pipeline = event_dict["detail"]["pipeline"]
    pipeline_url = f"https://{region}.console.aws.amazon.com/codesuite/codepipeline/pipelines/{pipeline}/view?region={region}"

    # Send Slack webhook
    text = f"{message}\n<{pipeline_url}|Visit CodePipeline>"
    msg = {
        "text": text,
    }
    encoded_msg = json.dumps(msg).encode("utf-8")
    resp = http.request("POST", SLACK_WEBHOOK_URL, body=encoded_msg)
    print({"statusCode": resp.status, "body": "Send message."})

    return