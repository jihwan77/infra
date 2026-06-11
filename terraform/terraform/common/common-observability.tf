###############################
# CloudWatch Alarm → EventBridge → cvexpert-alarm-notifier
###############################

# 1) CloudWatch Alarm 상태변화 감지 Rule
resource "aws_cloudwatch_event_rule" "cvexpert_alarm_rule" {
  name        = "cvexpert-alarm-to-lambda"
  description = "Send CloudWatch Alarm events to Slack notifier Lambda"

  event_pattern = jsonencode({
    "source": ["aws.cloudwatch"],
    "detail-type": ["CloudWatch Alarm State Change"],
    "detail": {
      "state": {
        "value": ["ALARM"]
      },
      "alarmName": [
        { "prefix": "cvexpert-" }
      ]
    }
  })
}

###############################
# 2) 기존 Slack 알림 Lambda 가져오기
###############################

data "aws_lambda_function" "cvexpert_alarm_notifier" {
  function_name = "cvexpert-alarm-notifier"
}

###############################
# 3) EventBridge → Slack 알림 Lambda 타깃 연결
###############################

resource "aws_cloudwatch_event_target" "cvexpert_alarm_notifier_target" {
  rule      = aws_cloudwatch_event_rule.cvexpert_alarm_rule.name
  target_id = "cvexpert-alarm-notifier"
  arn       = data.aws_lambda_function.cvexpert_alarm_notifier.arn
}

###############################
# 4) EventBridge가 Slack Lambda 호출 권한 부여
###############################

resource "aws_lambda_permission" "allow_eventbridge_to_invoke_alarm_notifier" {
  statement_id  = "AllowExecutionFromEventBridgeAlarmNotifier"
  action        = "lambda:InvokeFunction"
  function_name = data.aws_lambda_function.cvexpert_alarm_notifier.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.cvexpert_alarm_rule.arn
}

