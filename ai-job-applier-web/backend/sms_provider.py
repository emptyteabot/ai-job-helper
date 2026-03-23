import logging
import os
from typing import Callable

logger = logging.getLogger(__name__)


def _mask_phone(phone: str) -> str:
    digits = "".join(ch for ch in str(phone or "") if ch.isdigit())
    if not digits:
        return "unknown phone"
    if len(digits) <= 4:
        return digits
    return f"***{digits[-4:]}"


def _mask_code(code: str) -> str:
    if not code:
        return "xxxxxx"
    return f"***{code[-2:]}" if len(code) > 2 else code


def _normalize_e164(phone: str, default_country_code: str = "86") -> str:
    raw = str(phone or "").strip()
    if not raw:
        return raw
    if raw.startswith("+"):
        digits = "".join(ch for ch in raw if ch.isdigit())
        return f"+{digits}" if digits else raw
    digits = "".join(ch for ch in raw if ch.isdigit())
    if not digits:
        return raw
    if digits.startswith("00") and len(digits) > 2:
        return f"+{digits[2:]}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{default_country_code}{digits}"
    return f"+{digits}"


def _noop_delivery(phone: str, code: str) -> bool:
    logger.debug("SMS delivery skipped for %s because provider is not configured", _mask_phone(phone))
    return False


def _log_delivery(phone: str, code: str) -> bool:
    logger.info("Simulated SMS for %s via console logger, code=%s", _mask_phone(phone), _mask_code(code))
    return True


class SmsProvider:
    def __init__(
        self,
        key: str,
        name: str,
        configured: bool,
        help_text: str,
        deliver_fn: Callable[[str, str], bool],
    ):
        self.key = key
        self.name = name
        self.configured = configured
        self.help_text = help_text
        self._deliver_fn = deliver_fn

    def send_code(self, phone: str, code: str) -> bool:
        return self._deliver_fn(phone, code)


def _missing_env_provider(key: str, name: str, missing: list[str], help_text: str) -> SmsProvider:
    return SmsProvider(
        key=key,
        name=name,
        configured=False,
        help_text=f"{help_text} Missing: {', '.join(missing)}.",
        deliver_fn=_noop_delivery,
    )


def _package_missing_provider(key: str, name: str, package_name: str, help_text: str) -> SmsProvider:
    return SmsProvider(
        key=key,
        name=name,
        configured=False,
        help_text=f"{help_text} Install package: {package_name}.",
        deliver_fn=_noop_delivery,
    )


def _build_tencentcloud_provider() -> SmsProvider:
    secret_id = os.getenv("TENCENT_SMS_SECRET_ID", "").strip()
    secret_key = os.getenv("TENCENT_SMS_SECRET_KEY", "").strip()
    app_id = os.getenv("TENCENT_SMS_APP_ID", "").strip()
    sign_name = os.getenv("TENCENT_SMS_SIGN_NAME", "").strip()
    template_id = os.getenv("TENCENT_SMS_TEMPLATE_ID", "").strip()
    region = os.getenv("TENCENT_SMS_REGION", "ap-guangzhou").strip() or "ap-guangzhou"
    endpoint = os.getenv("TENCENT_SMS_ENDPOINT", "sms.tencentcloudapi.com").strip() or "sms.tencentcloudapi.com"
    template_ttl_minutes = os.getenv("TENCENT_SMS_TEMPLATE_TTL_MINUTES", "10").strip() or "10"
    default_country_code = os.getenv("TENCENT_SMS_DEFAULT_COUNTRY_CODE", "86").strip() or "86"
    missing = [
        key
        for key, value in {
            "TENCENT_SMS_SECRET_ID": secret_id,
            "TENCENT_SMS_SECRET_KEY": secret_key,
            "TENCENT_SMS_APP_ID": app_id,
            "TENCENT_SMS_SIGN_NAME": sign_name,
            "TENCENT_SMS_TEMPLATE_ID": template_id,
        }.items()
        if not value
    ]
    help_text = "Configure Tencent Cloud SMS credentials, app ID, sign, and template before enabling production SMS."
    if missing:
        return _missing_env_provider("tencentcloud", "Tencent Cloud SMS", missing, help_text)

    try:
        from tencentcloud.common import credential
        from tencentcloud.common.profile.client_profile import ClientProfile
        from tencentcloud.common.profile.http_profile import HttpProfile
        from tencentcloud.sms.v20210111 import models, sms_client
    except ImportError:
        return _package_missing_provider("tencentcloud", "Tencent Cloud SMS", "tencentcloud-sdk-python", help_text)

    cred = credential.Credential(secret_id, secret_key)
    http_profile = HttpProfile()
    http_profile.endpoint = endpoint
    client_profile = ClientProfile()
    client_profile.httpProfile = http_profile
    client = sms_client.SmsClient(cred, region, client_profile)

    def _deliver(phone: str, code: str) -> bool:
        normalized_phone = _normalize_e164(phone, default_country_code=default_country_code)
        req = models.SendSmsRequest()
        req.SmsSdkAppId = app_id
        req.SignName = sign_name
        req.TemplateId = template_id
        req.TemplateParamSet = [str(code), str(template_ttl_minutes)]
        req.PhoneNumberSet = [normalized_phone]
        try:
            response = client.SendSms(req)
            payload = response.to_json_string()
            logger.info("Tencent Cloud SMS response for %s: %s", _mask_phone(normalized_phone), payload)
            return '"Code":"Ok"' in payload or '"SendStatusSet"' in payload
        except Exception as exc:
            logger.warning("Tencent Cloud SMS send failed for %s: %s", _mask_phone(normalized_phone), exc, exc_info=True)
            return False

    return SmsProvider(
        key="tencentcloud",
        name="Tencent Cloud SMS",
        configured=True,
        help_text="Using Tencent Cloud SMS. Ensure the template parameters match: verification code, validity minutes.",
        deliver_fn=_deliver,
    )


def _build_twilio_provider() -> SmsProvider:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    from_number = os.getenv("TWILIO_FROM_NUMBER", "").strip()
    default_country_code = os.getenv("TWILIO_DEFAULT_COUNTRY_CODE", "86").strip() or "86"
    missing = [
        key
        for key, value in {
            "TWILIO_ACCOUNT_SID": account_sid,
            "TWILIO_AUTH_TOKEN": auth_token,
            "TWILIO_FROM_NUMBER": from_number,
        }.items()
        if not value
    ]
    help_text = "Configure a Twilio account SID, auth token, and sender number before enabling production SMS."
    if missing:
        return _missing_env_provider("twilio", "Twilio SMS", missing, help_text)

    try:
        from twilio.rest import Client
    except ImportError:
        return _package_missing_provider("twilio", "Twilio SMS", "twilio", help_text)

    client = Client(account_sid, auth_token)

    def _deliver(phone: str, code: str) -> bool:
        normalized_phone = _normalize_e164(phone, default_country_code=default_country_code)
        body = f"AgentHelpJob code: {code}. Valid for 10 minutes."
        try:
            message = client.messages.create(body=body, from_=from_number, to=normalized_phone)
            logger.info("Twilio SMS sent for %s sid=%s status=%s", _mask_phone(normalized_phone), message.sid, message.status)
            return bool(message.sid)
        except Exception as exc:
            logger.warning("Twilio SMS send failed for %s: %s", _mask_phone(normalized_phone), exc, exc_info=True)
            return False


    return SmsProvider(
        key="twilio",
        name="Twilio SMS",
        configured=True,
        help_text="Using Twilio SMS messaging. Ensure your sender is approved for the target region.",
        deliver_fn=_deliver,
    )


def resolve_sms_provider(provider_key: str) -> SmsProvider:
    normalized = (provider_key or "").strip().lower()
    if normalized in {"log", "console"}:
        return SmsProvider(
            key="console",
            name="Console SMS logger",
            configured=True,
            help_text="Codes are only logged for internal review; enable a real provider to reach devices.",
            deliver_fn=_log_delivery,
        )
    if normalized in {"tencent", "tencentcloud", "tencent_cloud"}:
        return _build_tencentcloud_provider()
    if normalized in {"twilio"}:
        return _build_twilio_provider()
    if not normalized:
        return SmsProvider(
            key="none",
            name="SMS delivery disabled",
            configured=False,
            help_text="Set AUTH_SMS_PROVIDER to tencentcloud or twilio to enable real SMS delivery.",
            deliver_fn=_noop_delivery,
        )
    return SmsProvider(
        key=normalized,
        name=f"Unimplemented provider ({normalized})",
        configured=False,
        help_text="This provider key is recognized but no integration is wired yet.",
        deliver_fn=_noop_delivery,
    )
