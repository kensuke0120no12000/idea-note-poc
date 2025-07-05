# PoC: 動的知覚・推論システム

このプロジェクトは、「二重ループ・アーキテクチャ」の概念実証（PoC）です。

## セットアップ手順

1.  **リポジトリをクローンします。**

2.  **仮想環境を作成して有効化します。**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Mac/Linux
    # venv\\Scripts\\activate  # Windows
    ```

3.  **必要なライブラリをインストールします。**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Google APIキーを設定します。**
    `.env`という名前のファイルをプロジェクトルート（`PoC_Sandbox`内）に作成し、以下の内容を記述します。
    ```
    GOOGLE_API_KEY="your_api_key_here"
    ```

## 実行方法

1.  **APIサーバーを起動します。**
    ```bash
    uvicorn app.main:app --reload --app-dir アイデアノート/PoC_Sandbox
    ```
    > **Note:** プロジェクトのルートから実行するため、`--app-dir` オプションでアプリケーションのディレクトリを指定しています。

2.  ブラウザで `http://127.0.0.1:8000/docs` を開くと、APIのドキュメント（Swagger UI）が表示されます。

## 手動テスト手順

Swagger UI (`http://127.0.0.1:8000/docs`) を使って、以下の手順で動作確認ができます。

1.  **ダミーイベントの生成と処理**
    *   `POST /events/generate_and_process/` を開きます。
    *   "Try it out" ボタンをクリックし、"Execute" ボタンをクリックします。
    *   レスポンスとして、処理されたイベント情報と、それに対するAIの推論結果（アクション提案）が返ってくることを確認します。

2.  **イベントリストの取得**
    *   `GET /events/` を開きます。
    *   "Try it out" -> "Execute" をクリックします。
    *   手順1で作成されたイベントを含む、イベントのリストが返ってくることを確認します。

3.  **特定のイベントの登録と推論**
    *   `POST /events/` を開きます。
    *   "Try it out" ボタンをクリックします。
    *   リクエストボディに、以下のようなJSONを入力して "Execute" をクリックします。
        ```json
        {
          "event_type": "system_alert",
          "raw_event": {
            "service": "database",
            "severity": "critical",
            "message": "Database connection lost. Immediate action required."
          }
        }
        ```
    *   レスポンスとして、`critical`アラートに対応するアクション（例: インシデントチームの招集など）が`notes`フィールドに追記されていることを確認します。 