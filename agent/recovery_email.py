"""Branded reset email with plain-text fallback and no remote tracking assets."""
from html import escape
def content(link):
    safe=escape(link,quote=True)
    text=('AgentShield AI | Account recovery\n\nYou requested a password reset for your private AgentShield workspace.\n\n'
          '1. Open this one-time link within 15 minutes:\n'+link+'\n\n'
          '2. Choose a unique password of 12–128 characters.\n3. Sign in again with your new password.\n\n'
          'After a successful reset, all previous sign-in sessions and browser extension pairings are revoked. Your saved invoices and audit records stay in your account.\n\n'
          'Did not request this? Ignore this email. Your password has not changed. Never share this link or paste it into Zivvi, invoice chat or a public demo.\n\n'
          'AgentShield AI — Intelligence with boundaries. Synthetic finance sandbox; no real bank accounts or money movement.')
    html=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Reset your AgentShield password</title></head>
<body style="margin:0;padding:0;background-color:#edf2fa;font-family:Arial,Helvetica,sans-serif;color:#1c3452">
<div style="display:none;max-height:0;overflow:hidden">Your one-time AgentShield reset link expires in 15 minutes. Keep it private.</div>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#edf2fa"><tr><td align="center" style="padding:32px 14px">
<table role="presentation" width="600" cellspacing="0" cellpadding="0" style="width:100%;max-width:600px;background-color:#ffffff;border:1px solid #d6e0ee;border-radius:22px">
<tr><td style="padding:30px 32px;background-color:#173c66;background-image:linear-gradient(120deg,#173c66,#5149aa);border-radius:22px 22px 0 0">
<table role="presentation" cellspacing="0" cellpadding="0"><tr><td width="48" height="48" align="center" style="background-color:#b6f0e1;color:#173c66;border-radius:14px;font-size:20px;font-weight:bold">AS</td><td style="padding-left:13px;color:#ffffff;font-size:23px;font-weight:bold">AgentShield AI<br><span style="font-size:10px;font-weight:normal;letter-spacing:2px;color:#c8e6f7">INTELLIGENCE WITH BOUNDARIES</span></td></tr></table>
<p style="margin:28px 0 0;font-size:11px;font-weight:bold;letter-spacing:2px;color:#b6f0e1">YOUR WORKSPACE. YOUR CONTROL.</p></td></tr>
<tr><td style="padding:32px"><h1 style="margin:0 0 17px;font-size:29px;line-height:1.25;letter-spacing:-1px;color:#193858">Let's get you back in.</h1>
<p style="font-size:15px;line-height:1.8;color:#49627d;margin:0 0 22px">We received a request to reset your AgentShield password. Choose a new password and return to your private workspace.</p>
<table role="presentation" cellspacing="0" cellpadding="0"><tr><td bgcolor="#3655c5" style="border-radius:11px"><a href="{safe}" style="display:inline-block;padding:16px 25px;color:#ffffff;text-decoration:none;font-size:15px;font-weight:bold;border:1px solid #3655c5;border-radius:11px">Reset my password &#8594;</a></td></tr></table>
<p style="margin:20px 0;padding:10px 13px;background-color:#fff3da;color:#705017;font-size:12px;line-height:1.6;border-radius:8px"><b>15 minutes. One use.</b> Request a new link if this one expires.</p>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#eff5fc;border-radius:12px"><tr><td style="padding:18px 20px;color:#314e6b;font-size:13px;line-height:1.9"><b style="color:#193858">What happens next</b><br>1. Open your private reset link.<br>2. Choose a unique password of 12–128 characters.<br>3. Sign in again with your new password.</td></tr></table>
<p style="font-size:13px;line-height:1.8;color:#49627d;margin:22px 0">A successful reset signs out previous sessions and revokes browser extension pairings. Your saved invoices and audit history stay in your account.</p>
<h2 style="font-size:15px;margin:24px 0 8px;color:#193858">Didn't request this?</h2><p style="font-size:13px;line-height:1.8;color:#49627d;margin:0">You can ignore this email. Your password has not changed. Keep the link private—never share it with anyone or paste it into Zivvi, invoice chat or a public demo.</p>
<div style="margin-top:25px;padding-top:20px;border-top:1px solid #dce5ef"><p style="font-size:11px;line-height:1.7;color:#5b7189;margin:0 0 8px">Button not working? Copy this entire link into your browser:</p><a href="{safe}" style="font-size:11px;line-height:1.7;color:#3655a1;word-break:break-all;overflow-wrap:anywhere">{safe}</a></div></td></tr>
<tr><td style="padding:20px 32px;background-color:#f5f8fc;border-radius:0 0 22px 22px;color:#61758d;font-size:11px;line-height:1.8"><b style="color:#304d6b">AgentShield AI</b> &middot; A visible boundary for AI actions.<br>Synthetic finance sandbox. No real bank connections or money movement.<br>This is an automated account-security email.</td></tr>
</table></td></tr></table></body></html>'''
    return text,html
