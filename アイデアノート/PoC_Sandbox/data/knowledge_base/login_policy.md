# ユーザーログインに関するポリシー

## 通常ログイン
- ユーザーIDとパスワードによる認証を必須とする。
- ログイン成功時、最終ログイン日時を記録する。

## 不審なログイン試行
- 同一IPアドレスから5分以内に10回以上のログイン失敗があった場合、そのIPを一時的にブロックする。
- 普段と異なる国や地域からのログインが検知された場合、ユーザーに確認通知を送信する。
- 通知には、ログインがあった日時、場所、デバイス情報を含めること。 