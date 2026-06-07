# Contributing to Matrix Authenticated Compiler

Matrix Authenticated Compilerへのご貢献ありがとうございます！

このドキュメントでは、プロジェクトに貢献するためのガイドラインを説明します。

## 📋 行動規範

このプロジェクトに参加することで、私たちの[Code of Conduct](./CODE_OF_CONDUCT.md)に同意したことになります。

## 🚀 貢献方法

### 報告（Issues）

バグを見つけたり、改善提案がある場合は、[Issues](https://github.com/yourusername/matrix-authenticated-compiler/issues)を作成してください。

**Issue を作成する前に：**
- 既存のIssueで報告されていないか確認してください
- バグリポートには再現手順を含めてください
- テスト環境情報（Python version、OS等）を記載してください

### Pull Requests

Pull Requestは大歓迎です！

**プロセス：**

1. **リポジトリをFork**
   ```bash
   git clone https://github.com/yourusername/matrix-authenticated-compiler.git
   cd matrix-authenticated-compiler
   ```

2. **Feature ブランチを作成**
   ```bash
   git checkout -b feature/your-amazing-feature
   ```

3. **変更を加える**
   ```bash
   # コードを編集
   # テストを追加
   # ドキュメントを更新
   ```

4. **テストを実行**
   ```bash
   pytest
   pytest --cov=matrix_authenticated_compiler
   ```

5. **コード品質をチェック**
   ```bash
   black .
   flake8 .
   mypy .
   ```

6. **変更をCommit**
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```

7. **ブランチにPush**
   ```bash
   git push origin feature/your-amazing-feature
   ```

8. **Pull Requestを作成**
   - GitHubで自動的にPull Requestを作成するオプションが表示されます
   - テンプレートに従って詳細を記入してください
   - テストが全てパスしていることを確認してください

### Pull Request テンプレート

```markdown
## Description
変更の簡潔な説明

## Related Issues
- Fixes #(issue)
- Related to #(issue)

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
変更のテスト方法を説明

## Checklist
- [ ] コードが PEP 8 に準拠
- [ ] テストを追加/更新した
- [ ] ドキュメントを更新した
- [ ] ローカルでテストが成功
```

## 🛠️ 開発環境セットアップ

### 環境構築

```bash
# Python 3.8+ が必要です
python --version

# 仮想環境を作成
python -m venv venv

# 仮想環境を有効化
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt

# 開発用依存関係もインストール
pip install -e .
```

### テスト実行

```bash
# 全テストを実行
pytest

# カバレッジレポート付き
pytest --cov=matrix_authenticated_compiler

# 特定のテストを実行
pytest tests/test_authenticator.py

# 詳細出力
pytest -vv
```

### コード品質チェック

```bash
# Black でコードをフォーマット
black .

# Flake8 でスタイルをチェック
flake8 .

# MyPy で型チェック
mypy .

# 全て実行
black . && flake8 . && mypy . && pytest
```

## 📖 コーディング規約

### Python スタイルガイド

- [PEP 8](https://www.python.org/dev/peps/pep-0008/) に準拠
- [Black](https://github.com/psf/black) でフォーマット
- Line length: 88 characters

### コメント・ドキュメント

```python
def authenticate_multi_layer(self, context: AuthenticationContext) -> Dict[str, bytes]:
    """
    多層認証キーを導出する
    
    Args:
        context: 認証コンテキスト (device_seed, os_seed, app_seed)
    
    Returns:
        認証キーの辞書 {'device': bytes, 'os': bytes, 'application': bytes}
    
    Raises:
        ValueError: コンテキストが無効な場合
    
    Examples:
        >>> auth_keys = authenticator.authenticate_multi_layer(context)
        >>> print(len(auth_keys['device']))
        32
    """
    # 実装...
```

### タイプヒント

```python
from typing import Dict, List, Optional, Tuple

def compile(self, 
           source_code: str,
           context: AuthenticationContext) -> Tuple[bytes, Dict[str, Any]]:
    """コンパイルを実行"""
    pass
```

## 📝 コミットメッセージ規約

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type
- **feat**: 新機能
- **fix**: バグ修正
- **docs**: ドキュメント
- **style**: コードスタイル
- **refactor**: リファクタリング
- **test**: テスト追加
- **perf**: パフォーマンス改善

### Example
```
feat(authenticator): add support for custom key derivation

- Implement PBKDF2 alternative to existing KDF
- Add configuration option for iterations
- Update tests for new functionality

Closes #42
```

## 🔐 セキュリティについて

### セキュリティの脆弱性を見つけた場合

**公開Issueを作成しないでください。**

代わりに、プロジェクトメンテナーに直接報告してください：

```
Email: security@example.com
Subject: [SECURITY] Vulnerability Report
```

報告は機密扱いにされ、迅速に対応されます。

## 📚 ドキュメント

### 新機能を追加する場合

1. **docstring を追加**
   ```python
   def new_feature(self, param: str) -> bool:
       """新機能の説明
       
       Args:
           param: パラメータの説明
       
       Returns:
           結果の説明
       """
       pass
   ```

2. **README.md を更新**
   ```markdown
   ## New Feature
   
   説明とユースケース
   ```

3. **適切なドキュメントファイルを更新**
   - INTEGRATION_GUIDE.md
   - MATRIX_COMPILER_DOCUMENTATION.md

## 🎯 開発優先度

現在の優先度：

### High Priority
- [ ] セキュリティ脆弱性の修正
- [ ] クリティカルなバグの修正
- [ ] テストカバレッジの改善

### Medium Priority
- [ ] パフォーマンス最適化
- [ ] ドキュメント改善
- [ ] コード品質向上

### Low Priority
- [ ] 新機能の提案
- [ ] マイナーな改善

## 🏆 貢献者リスト

すべての貢献者は以下に記載されます：

- [Contributors List](./CONTRIBUTORS.md)

## 📞 質問・相談

- **GitHub Issues**: バグ報告・機能リクエスト
- **GitHub Discussions**: アイデア・設計相談
- **Email**: maintainers@example.com

## ✅ チェックリスト

PRを作成する前に確認：

- [ ] Code of Conduct を読んだ
- [ ] ローカルでテストが成功している
- [ ] コード品質チェック (black, flake8, mypy) が成功している
- [ ] ドキュメントを更新した
- [ ] コミットメッセージが明確である
- [ ] 関連するIssueをリンクした

---

ご協力ありがとうございます！🙏

Matrix Authenticated Compiler をより良いプロジェクトにするのをお手伝いください。
