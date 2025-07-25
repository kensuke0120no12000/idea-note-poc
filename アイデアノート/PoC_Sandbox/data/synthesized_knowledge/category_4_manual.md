# 提案するカテゴリ名: **基盤サービス障害** 対応マニュアル\n# 基盤サービス障害 対応マニュアル

## 問題の概要

このカテゴリの問題は、アプリケーション層ではなく、その下位にある共有インフラストラクチャ（データベース、サーバーノード、ネットワークなど）に起因する広範囲なサービス障害を指します。提供されたログからは、主に以下の2つの基盤レベルの問題が複合的に発生していることが示唆されます。

1.  **データベース接続タイムアウト**: 複数のサービス（`api_gateway`, `auth_service`, `database`）でデータベースへの接続がタイムアウトしている。これはデータベースサーバーの過負荷、ネットワーク問題、またはデータベース自体の健全性問題を示唆します。
2.  **ディスク容量不足**: 特定のサーバーノード（`node-A`）でディスク容量が危機的に低い状態であり、これが`api_gateway`, `database`, `inventory_service`など複数のサービスに影響を与えています。特に`database`サービス自身がディスク容量不足を報告していることから、データベースの動作に直接的な影響を与えている可能性が高いです。

これらの問題は、単一のサービス障害に留まらず、システム全体の可用性やパフォーマンスに深刻な影響を及ぼす可能性があります。

## 考えられる根本原因

提供されたログから推測される根本原因は以下の通りです。

*   **データベースサーバーのリソース枯渇**:
    *   **ディスク容量不足**: `node-A`のディスク容量不足が直接的にデータベースサービスに影響を与え、データベースのログ書き込み、一時ファイルの作成、データファイルの拡張などができなくなり、結果としてデータベースの応答遅延や接続タイムアウトを引き起こしている可能性が非常に高いです。
    *   **CPU/メモリ/I/Oの過負荷**: データベースサーバーが処理能力を超えたリクエストを受けている、または非効率なクエリが実行されているために、CPU、メモリ、ディスクI/Oが飽和状態になり、接続処理が遅延している。
    *   **接続プールの枯渇**: アプリケーション側のデータベース接続プール設定が不適切であるか、データベースサーバーが許容できる接続数を超過している。
*   **ネットワーク問題**:
    *   アプリケーションサーバーとデータベースサーバー間のネットワーク遅延、パケットロス、または帯域幅の不足。
*   **アプリケーションの不具合**:
    *   データベース接続を適切に解放しない、または過剰な接続を確立するアプリケーションのバグ。
    *   非効率なデータベースクエリが頻繁に実行され、データベースに過度な負荷をかけている。
*   **監視・アラート体制の不備**:
    *   ディスク容量やデータベースの健全性に関するアラートが適切に設定されていなかった、または閾値が高すぎて手遅れになるまで検知できなかった。
    *   容量計画が不十分で、リソースの枯渇が予測できなかった。

## ビジネスへの影響

この問題が引き起こす可能性のあるビジネスへの影響は以下の通りです。

*   **サービス利用不可/機能停止**: API Gateway、認証サービス、インベントリサービスなど、複数の基幹サービスが影響を受けるため、ユーザーはログイン、データ参照、トランザクション実行などの主要な機能を利用できなくなります。
*   **ユーザー体験の著しい低下**: 応答時間の遅延、エラーページの表示、操作の失敗などにより、ユーザーは不満を感じ、サービスから離脱する可能性があります。
*   **売上機会の損失**: Eコマースサイトであれば購入手続きが完了できない、SaaSであれば顧客がサービスを利用できないなど、直接的な売上損失につながります。
*   **顧客満足度とブランドイメージの毀損**: サービスが不安定であるという認識が広まり、顧客からの信頼を失い、ブランドイメージが低下します。
*   **SLA（サービスレベル契約）違反**: サービスの可用性が低下することで、顧客とのSLAに違反し、契約上のペナルティが発生する可能性があります。
*   **運用コストの増加**: 問題の調査、復旧、恒久対策に多くのエンジニアリングリソースが割かれ、運用コストが増加します。

## 推奨される一次対応

問題発生時にエンジニアが最初に行うべき具体的な確認手順や応急処置をリストアップします。

1.  **アラートの確認と影響範囲の特定**:
    *   関連する監視システム（Prometheus, Grafana, Datadogなど）で、CPU使用率、メモリ使用率、ディスクI/O、ネットワーク帯域、データベース接続数、スロークエリ、エラーレートなどのメトリクスを確認します。
    *   特に`node-A`のディスク使用率を最優先で確認し、飽和状態であればその原因（ログファイル、一時ファイル、データファイルなど）を特定します。
    *   影響を受けているサービス（API Gateway, Auth Serviceなど）のエラーレートやレイテンシの急増を確認し、影響範囲を特定します。
2.  **リソース状況の緊急確認**:
    *   **`node-A`のディスク容量解放**: SSHで`node-A`にログインし、`df -h`でディスク使用率を確認。`du -sh /*`などで大容量のディレクトリを特定し、不要なログファイルや一時ファイルを削除して緊急的にディスク容量を確保します。
    *   **データベースサーバーの健全性確認**:
        *   データベースサーバーのCPU、メモリ、ディスクI/O、ネットワーク使用率を確認します。
        *   データベースの接続数、アクティブなセッション、ロック状況、スロークエリを確認します。
        *   データベースのログファイルにエラーや警告が出ていないか確認します。
3.  **応急処置**:
    *   **ディスク容量不足の場合**:
        *   不要なログファイル、バックアップファイル、一時ファイルの削除。
        *   可能であれば、ディスクのオンライン拡張を試みる（クラウド環境の場合）。
    *   **データベース過負荷の場合**:
        *   緊急性の低いバッチ処理やレポート生成クエリの一時停止。
        *   リードレプリカへのトラフィック分散（設定済みの場合）。
        *   アプリケーション側のデータベース接続プール設定の見直し（一時的な上限緩和など、ただし慎重に）。
        *   キャッシュのクリアや再構築（該当する場合）。
    *   **サービス再起動**: 影響を受けているサービス（例: `api_gateway`, `auth_service`）を再起動し、一時的に接続をリフレッシュする。ただし、根本原因が解決しない限り、再発する可能性が高い。
    *   **フェイルオーバー**: 冗長構成が組まれている場合、健全なノードへのフェイルオーバーを検討します。
4.  **情報収集と記録**:
    *   発生時刻、影響範囲、確認したメトリクス、実行したコマンド、その結果などを詳細に記録します。これは事後分析（Post-Mortem）に不可欠です。
    *   関係者への状況共有を適宜行います。

## 恒久的な解決策/予防策

この問題を将来的に防ぐための、より根本的な解決策やアーキテクチャの改善案を提案します。

1.  **監視とアラートの強化**:
    *   **多角的なメトリクス監視**: ディスク容量、CPU、メモリ、ネットワークI/O、データベース接続数、クエリ実行時間、レプリケーション遅延など、基盤サービスの健全性を示す主要なメトリクスを網羅的に監視します。
    *   **適切なアラート閾値の設定**: 閾値を適切に設定し、問題が深刻化する前に早期にアラートを発報する体制を構築します。特にディスク容量については、`warning`（例: 70%）、`error`（例: 85%）、`critical`（例: 95%）など段階的なアラートを設定します。
    *   **予測的監視と容量計画**: 過去のトレンドデータに基づき、将来のリソース枯渇を予測し、事前にリソース増強や最適化を行う容量計画を定期的に実施します。
2.  **リソース管理と自動化**:
    *   **ディスククリーンアップの自動化**: ログファイルや一時ファイルのローテーション、アーカイブ、自動削除を定期的に実行する仕組みを導入します。
    *   **オートスケーリング**: データベースのリードレプリカやアプリケーションサーバーなど、負荷に応じて自動的にリソースを増減させるオートスケーリングを導入し、急激なトラフィック増加に対応できるようにします。
    *   **リソースのプロビジョニング自動化**: Infrastructure as Code (IaC) を活用し、必要に応じて迅速かつ確実にリソースを拡張できる体制を整えます。
3.  **データベースの最適化と高可用性**:
    *   **クエリの最適化**: スロークエリの特定と改善（インデックスの追加、クエリのリファクタリング、ORMの適切な利用など）を継続的に行い、データベースへの負荷を軽減します。
    *   **接続プールの最適化**: アプリケーション側のデータベース接続プール設定を適切に見直し、データベースの負荷とアプリケーションの要件のバランスを取ります。
    *   **データベースの冗長化とクラスタリング**: マスター/スレーブ構成、リードレプリカ、またはデータベースクラスタリングを導入し、単一障害点（SPOF）を排除し、高可用性を確保します。
    *   **データベースのシャーディング/パーティショニング**: データ量が増大した場合に、データベースを水平分割することで負荷を分散し、スケーラビリティを向上させます。
4.  **アーキテクチャの改善**:
    *   **マイクロサービス間の疎結合化**: サービス間の依存関係を最小限に抑え、あるサービスの障害が他のサービスに波及しないよう、障害分離の原則を徹底します。
    *   **サーキットブレーカーとリトライメカニズム**: 外部サービス（データベースを含む）への呼び出しにサーキットブレーカーを導入し、障害発生時に過度なリトライによる負荷集中を防ぎます。また、適切なリトライ戦略を実装します。
    *   **キャッシュの活用**: 頻繁にアクセスされるデータをキャッシュすることで、データベースへの負荷を軽減し、応答速度を向上させます。
5.  **定期的なメンテナンスとレビュー**:
    *   **ログローテーションとアーカイブ**: ログファイルの肥大化を防ぐため、定期的なローテーションとアーカイブを徹底します。
    *   **データベースのメンテナンス**: インデックスの再構築、統計情報の更新、不要なデータのパージなどを定期的に行い、データベースのパフォーマンスを維持します。
    *   **事後分析（Post-Mortem）の実施**: 障害発生時には必ず事後分析を行い、根本原因を特定し、再発防止策を立案・実行します。
    *   **カオスエンジニアリング**: 意図的に障害を注入し、システムの回復力や監視・アラートの有効性をテストすることで、未知の障害に対する耐性を高めます。