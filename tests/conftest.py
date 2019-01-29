import sys

collect_ignore = []
if sys.version_info[0] > 2:
    collect_ignore.extend([
        'test_api_2stepinit.py',
        'test_api_applications.py',
        'test_api_audit.py',
        'test_api_clienttype.py',
        'test_api_lib_policy.py',
        'test_api_machines.py',
        'test_api_periodictask.py',
        'test_api_policy.py',
        'test_api_register.py',
        'test_api_roles.py',
        'test_api_smtpserver.py',
        'test_api_subscriptions.py',
        'test_api_system.py',
        'test_api_token.py',
        'test_api_ttype.py',
        'test_api_u2f.py',
        'test_api_users.py',
        'test_api_validate.py',
        'test_lib_applications.py',
        'test_lib_apps.py',
        'test_lib_caconnector.py',
        'test_lib_challenges.py',
        'test_lib_importotp.py',
        'test_lib_machines.py',
        'test_lib_machinetokens.py',
        'test_lib_smsprovider.py',
        'test_lib_tokenclass.py',
        'test_lib_token.py',
        'test_lib_tokens_certificate.py',
        'test_lib_tokens_daplug.py',
        'test_lib_tokens_email.py',
        'test_lib_tokens_foureyes.py',
        'test_lib_tokens_hotp.py',
        'test_lib_tokens_motp.py',
        'test_lib_tokens_paper.py',
        'test_lib_tokens_passwordtoken.py',
        'test_lib_tokens_questionnaire.py',
        'test_lib_tokens_radius.py',
        'test_lib_tokens_remote.py',
        'test_lib_tokens_sms.py',
        'test_lib_tokens_ssh.py',
        'test_lib_tokens_tan.py',
        'test_lib_tokens_tiqr.py',
        'test_lib_tokens_totp.py',
        'test_lib_tokens_u2f.py',
        'test_lib_tokens_vasco.py',
        'test_lib_tokens_yubico.py',
        'test_lib_tokens_yubikey.py',
        'test_lib_usercache.py',
        'test_lib_utils.py',
        'test_mod_apache.py',
        'test_resolver_realm.py',
        'test_ui_certificate.py',
        'test_ui_login.py',
    ])
