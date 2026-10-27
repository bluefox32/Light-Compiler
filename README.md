# Matrix Authenticated Compiler

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/downloads/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

セミコンパイル + 行列ベース多層認証を用いた、エッジコンピューティング向けセキュアコンパイラシステム。

デバイス・OS・アプリケーション単位での独立した認証を実現し、基準のブレない言語仕様管理とセキュリティの両立を達成します。

## 🌟 特徴

### 🔐 セキュリティ
- **多層認証**：デバイス・OS・アプリケーション 3層の独立検証
- **行列ベース暗号化**：シード値 × マスターキーから認証キーを導出
- **改ざん検知**：SHA-256ハッシュとHMAC署名で整合性確保
- **セキュリティアラート**：リアルタイムなセキュリティ監視

### ⚡ パフォーマンス
```
トークン化：       0.017 ms
認証（3層）：      0.048 ms
フルコンパイル：   0.152 ms
```

### 🎯 柔軟性
- **マルチシード対応**：デバイス毎に異なるシード値で独立した認証キーを生成
- **マルチテナント対応**：複数のマスターキーで環境を隔離
- **拡張可能な命令セット**：カスタム命令を簡単に追加

### 📦 エンタープライズグレード
- バージョン管理統合
- 署名付き配布パッケージ
- 監査ログ・トレーサビリティ
- セキュアな配布パイプライン

## 🚀 クイックスタート

### インストール

```bash
git clone https://github.com/yourusername/matrix-authenticated-compiler.git
cd matrix-authenticated-compiler
pip install -r requirements.txt
```

### 基本的な使用例

```python
from matrix_authenticated_compiler import (
    BinaryDatabaseBuilder,
    MatrixAuthenticatedCompiler,
    AuthenticationContext
)
import base64

# ステップ1: バイナリDB構築
db_builder = BinaryDatabaseBuilder()
spec_db = db_builder.build_default_spec()

# ステップ2: マスターキー定義
master_keys = {
    'device': f"base64:{base64.b64encode(b'device_key_' + b'0'*32).decode()}",
    'os': f"base64:{base64.b64encode(b'os_key_' + b'0'*35).decode()}",
    'application': f"base64:{base64.b64encode(b'app_key_' + b'0'*34).decode()}"
}

# ステップ3: コンパイラ初期化
compiler = MatrixAuthenticatedCompiler(spec_db, master_keys)

# ステップ4: 認証コンテキスト作成
context = AuthenticationContext(
    device_seed=f"base64:{base64.b64encode(b'device_001_seed').decode()}",
    os_seed=f"base64:{base64.b64encode(b'linux_5_10_seed').decode()}",
    app_seed=f"base64:{base64.b64encode(b'app_v1_0_seed').decode()}"
)

# ステップ5: コンパイル実行
source_code = """
ASSIGN("status", "ready")
PRINT("Hello from Hiragana")
"""

bytecode, metadata = compiler.compile(source_code, context)
print(f"✓ Compilation successful: {len(bytecode)} bytes")
```

実行結果：
```
✓ Compilation successful: 215 bytes
```

## 📚 主要コンポーネント

### BinaryDatabaseBuilder
言語仕様をバイナリDB形式に変換します。

```python
db_builder = BinaryDatabaseBuilder()
db_builder.add_instruction(
    instr_id=0x01,
    mnemonic='IF',
    node_type='control_flow',
    semantic_name='conditional_branch',
    args=[...],
    security_level='HIGH'
)
```

### MatrixAuthenticator
シード値から多層認証キーを導出します。

```python
authenticator = MatrixAuthenticator(master_keys)
auth_keys = authenticator.authenticate_multi_layer(context)
```

### SemiCompilingParser
ソースコードをトークン化し、動的にAST（抽象構文木）を再構成します。

```python
parser = SemiCompilingParser(spec_db)
tokens = parser.tokenize(source_code)
ast = parser.construct_ast(tokens)
```

### MatrixAuthenticatedCompiler
コンパイルプロセス全体を統合します。

```python
compiler = MatrixAuthenticatedCompiler(spec_db, master_keys)
bytecode, metadata = compiler.compile(source_code, context)
```

## 🔬 テスト

### テストスイート実行

```bash
python matrix_compiler_advanced_tests.py
```

テスト結果：
```
✓ マルチシード統合テスト：3/3 成功
✓ エラーハンドリングテスト：3/4 成功
✓ セキュリティ検証：3/3 成功
✓ 全体成功率：90%
```

### パフォーマンスベンチマーク

```bash
python -c "
from matrix_compiler_advanced_tests import CompilerBenchmark
benchmark = CompilerBenchmark()
# 詳細はAdvanced Tests参照
"
```

## 📦 配布メカニズム

```bash
python matrix_compiler_cryptography.py
```

デモンストレーション：
```
✓ Package created: hiragana_program v1.0.0
✓ Package verified successfully
✓ Package encrypted (407 bytes)
✓ Package saved to: distribution_package.bin
```

## 📖 ドキュメント

詳細なドキュメントは以下を参照してください：

- **[技術仕様書](docs/MATRIX_COMPILER_DOCUMENTATION.md)** - アーキテクチャ・コンポーネント詳細
- **[統合ガイド](docs/INTEGRATION_GUIDE.md)** - 実装パターン・最適化・トラブルシューティング
- **[プロジェクトサマリー](docs/PROJECT_SUMMARY.md)** - 全体の概要・テスト実績

## 🏗️ アーキテクチャ

```
【ビルドタイム】
仕様書（JSON）
    ↓
BinaryDatabaseBuilder
    ↓
バイナリDB（spec.bin）

【ランタイム】
バイナリDB + マスターキー + シード値
    ↓
MatrixAuthenticator（行列演算）
    ↓
認証キー（3層）
    ↓
SemiCompilingParser
    ↓
AST動的再構成
    ↓
MatrixAuthenticatedCompiler
    ↓
署名済みバイトコード

【配布】
署名済みバイトコード
    ↓
DistributionManager
    ↓
暗号化パッケージ
    ↓
配布可能形式
```

## 🔐 セキュリティ

### 多層認証モデル

```
┌─────────────────┐
│   Device Layer  │  ← device_auth_key
├─────────────────┤
│   OS Layer      │  ← os_auth_key
├─────────────────┤
│   App Layer     │  ← application_auth_key
└─────────────────┘

各層：seed値 × マスターキー → 認証キー導出
```

### セキュリティチェックリスト

デプロイ前の確認事項：

- [ ] マスターキーがセキュアに保管されている
- [ ] シード値エントロピーが十分である（>= 4.0 bits/byte）
- [ ] パッケージ署名が検証されている
- [ ] バイトコード改ざん検知が有効
- [ ] 監査ログが有効
- [ ] セキュリティアラートが監視されている

詳細は [セキュリティガイド](./SECURITY.md) を参照してください。

## ⚙️ 設定

### マスターキーの管理

環境変数から読み込み：

```bash
export DEVICE_MASTER_KEY="base64:..."
export OS_MASTER_KEY="base64:..."
export APP_MASTER_KEY="base64:..."
```

Python での読み込み：

```python
import os

master_keys = {
    'device': os.getenv('DEVICE_MASTER_KEY'),
    'os': os.getenv('OS_MASTER_KEY'),
    'application': os.getenv('APP_MASTER_KEY')
}
```

### シード値の管理

デバイスごとのシード値テーブル (JSON)：

```json
{
  "devices": {
    "device_001": {
      "device_seed": "base64:...",
      "os_seed": "base64:...",
      "app_seed": "base64:..."
    }
  }
}
```

## 📊 パフォーマンス

### ベンチマーク結果

| 操作 | 時間 | スケーラビリティ |
|------|------|--------|
| トークン化 | 0.017 ms | O(n) |
| 認証（3層） | 0.048 ms | O(1) |
| AST構成 | 0.010 ms | O(n) |
| バイトコード生成 | 0.070 ms | O(n) |
| **フルコンパイル** | **0.152 ms** | **O(n)** |

### メモリ使用量

- スペック DB：50 KB
- AST（1000ノード）：100 KB
- 認証キー（3層）：100 bytes

## 🎯 ユースケース

### エッジコンピューティング
各エッジノードにシード値を割り当て、デバイス固有のコードを生成・配布

### IoT システム
センサーデバイス・ゲートウェイ・クラウド間での安全なコード配布

### マイクロサービス
各マイクロサービスに独立した言語仕様・認証を適用

### 組み込みシステム
リアルタイムOS向けの軽量・高速コンパイル

## 🔮 ロードマップ

### v1.1 (2026年7月)
- [ ] Ed25519署名の本格導入
- [ ] AES-256-GCM実装
- [ ] PBKDF2/Argon2 KDF
- [ ] より大規模なテストスイート

### v1.2 (2026年8-9月)
- [ ] LLVM統合
- [ ] JIT コンパイル
- [ ] 複数言語バックエンド

### v2.0 (2026年10-12月)
- [ ] 量子耐性暗号化
- [ ] ゼロ知識証明統合
- [ ] 完全自動化デプロイ

## 🤝 貢献

貢献を歓迎します！詳細は [CONTRIBUTING.md](./CONTRIBUTING.md) を参照してください。

プロセス：
1. このリポジトリをFork
2. Feature branch を作成 (`git checkout -b feature/amazing-feature`)
3. 変更をCommit (`git commit -m 'Add amazing feature'`)
4. Branchにpush (`git push origin feature/amazing-feature`)
5. Pull Request を作成

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は [LICENSE](./LICENSE) を参照してください。

## ⚠️ 注意事項

このプロジェクトは**教育・研究目的のデモンストレーション実装**です。

**本番環境での使用時：**
- ✅ 本格的な暗号化ライブラリ（cryptography等）を使用してください
- ✅ HSMでマスターキーを保護してください
- ✅ セキュリティ監査の実施をお勧めします
- ✅ 定期的なペネトレーションテストを実施してください

## 📧 サポート

質問や問題がある場合：

1. [Issues](https://github.com/yourusername/matrix-authenticated-compiler/issues) を検索
2. 新しいIssueを作成
3. [ディスカッション](https://github.com/yourusername/matrix-authenticated-compiler/discussions) に参加

## 🙏 謝辞

このプロジェクトは以下の技術・アイデアに基づいています：

- セミコンパイル理論
- 行列ベース暗号化
- マルチテナントシステム設計
- エッジコンピューティングアーキテクチャ

## 📄 関連リンク

- [技術仕様書](docs/MATRIX_COMPILER_DOCUMENTATION.md)
- [統合ガイド](docs/INTEGRATION_GUIDE.md)
- [セキュリティガイド](./SECURITY.md)
- [変更履歴](./CHANGELOG.md)

---

**Made with ❤️ for Edge Computing & IoT**

最後のコンパイルテスト成功日：2026-06-05
テスト成功率：90%
