"""
Matrix Authenticated Compiler
セミコンパイル + 行列ベース多層認証コンパイラ

シード値の行列とマスターキーから認証キーを導出し、
デバイス・OS・アプリケーション単位での多層認証を実現
"""

import numpy as np
import json
import hashlib
import base64
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import struct


class DataType(Enum):
    """データ型定義"""
    INTEGER = "int"
    FLOAT = "float"
    STRING = "string"
    BINARY = "binary"
    BLOCK = "block"
    BOOL = "bool"
    UNKNOWN = "unknown"


class AuthenticationLayer(Enum):
    """認証レイヤー定義"""
    DEVICE = "device"
    OS = "os"
    APPLICATION = "application"


@dataclass
class TokenInfo:
    """トークン情報"""
    instruction_id: int
    mnemonic: str
    args: List[Any]
    line: int
    column: int


@dataclass
class ASTNode:
    """AST ノード"""
    node_type: str
    semantic_name: str
    instruction_id: int
    args: List[Any]
    children: List['ASTNode']
    security_level: str
    
    def to_dict(self):
        return {
            'node_type': self.node_type,
            'semantic_name': self.semantic_name,
            'instruction_id': self.instruction_id,
            'args': self.args,
            'children': [c.to_dict() for c in self.children],
            'security_level': self.security_level
        }


@dataclass
class AuthenticationContext:
    """認証コンテキスト"""
    device_seed: str  # base64
    os_seed: str      # base64
    app_seed: str     # base64
    device_auth_key: Optional[bytes] = None
    os_auth_key: Optional[bytes] = None
    app_auth_key: Optional[bytes] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class BinaryDatabaseBuilder:
    """バイナリデータベース構築（ビルドタイム）"""
    
    def __init__(self):
        self.spec_db = {
            'version': '1.0',
            'instructions': {},
            'metadata': {}
        }
    
    def add_instruction(self, 
                       instr_id: int,
                       mnemonic: str,
                       node_type: str,
                       semantic_name: str,
                       args: List[Dict[str, Any]],
                       security_level: str = "MEDIUM",
                       forbidden_combinations: List[str] = None):
        """命令定義を追加"""
        
        self.spec_db['instructions'][instr_id] = {
            'mnemonic': mnemonic,
            'node_type': node_type,
            'semantic_name': semantic_name,
            'args': args,
            'security_level': security_level,
            'forbidden_combinations': forbidden_combinations or []
        }
    
    def build_default_spec(self) -> Dict:
        """デフォルト仕様書を構築"""
        
        # 制御フロー命令
        self.add_instruction(
            instr_id=0x01,
            mnemonic='IF',
            node_type='control_flow',
            semantic_name='conditional_branch',
            args=[
                {'name': 'condition', 'allowed_types': ['bool', 'int'], 'required': True},
                {'name': 'body', 'allowed_types': ['block'], 'required': True}
            ],
            security_level='HIGH'
        )
        
        self.add_instruction(
            instr_id=0x02,
            mnemonic='LOOP',
            node_type='control_flow',
            semantic_name='iterative_execution',
            args=[
                {'name': 'count', 'allowed_types': ['int'], 'required': True, 'min': 0, 'max': 1000000},
                {'name': 'body', 'allowed_types': ['block'], 'required': True}
            ],
            security_level='HIGH',
            forbidden_combinations=['LOOP']  # ネストループ禁止
        )
        
        self.add_instruction(
            instr_id=0x03,
            mnemonic='ASSIGN',
            node_type='variable_operation',
            semantic_name='variable_assignment',
            args=[
                {'name': 'variable', 'allowed_types': ['string'], 'required': True},
                {'name': 'value', 'allowed_types': ['int', 'float', 'string'], 'required': True}
            ],
            security_level='MEDIUM'
        )
        
        self.add_instruction(
            instr_id=0x04,
            mnemonic='PRINT',
            node_type='io_operation',
            semantic_name='output_statement',
            args=[
                {'name': 'expression', 'allowed_types': ['string', 'int', 'float'], 'required': True}
            ],
            security_level='LOW'
        )
        
        self.add_instruction(
            instr_id=0x05,
            mnemonic='CALL',
            node_type='function_call',
            semantic_name='function_invocation',
            args=[
                {'name': 'function_name', 'allowed_types': ['string'], 'required': True},
                {'name': 'arguments', 'allowed_types': ['block'], 'required': False}
            ],
            security_level='HIGH'
        )
        
        return self.spec_db
    
    def to_binary_db(self) -> bytes:
        """バイナリDB形式で出力"""
        import json
        return json.dumps(self.spec_db).encode('utf-8')
    
    def save(self, filepath: str):
        """ファイルに保存"""
        with open(filepath, 'wb') as f:
            f.write(self.to_binary_db())


class MatrixAuthenticator:
    """行列ベース認証エンジン"""
    
    def __init__(self, master_keys: Dict[str, str]):
        """
        master_keys: {
            'device': 'base64:...',
            'os': 'base64:...',
            'application': 'base64:...'
        }
        """
        self.master_keys = {
            layer: base64.b64decode(key.replace('base64:', ''))
            for layer, key in master_keys.items()
        }
    
    def seed_to_vector(self, seed_b64: str, vector_size: int = 32) -> np.ndarray:
        """シード値を数値ベクトルに変換"""
        
        seed_bytes = base64.b64decode(seed_b64.replace('base64:', ''))
        
        # シード値をハッシュで拡張
        hash_obj = hashlib.sha256(seed_bytes)
        for _ in range(5):
            hash_obj.update(hash_obj.digest())
        
        # ベクトルサイズに調整
        expanded = hash_obj.digest() * ((vector_size // 32) + 1)
        vector = np.frombuffer(expanded[:vector_size], dtype=np.uint8)
        
        return vector.astype(np.float64)
    
    def vector_to_key(self, vector: np.ndarray) -> bytes:
        """数値ベクトルを認証キーに変換"""
        
        # 正規化
        normalized = (vector % 256).astype(np.uint8)
        return normalized.tobytes()
    
    def matrix_multiply(self, 
                       seed_vector: np.ndarray,
                       master_vector: np.ndarray) -> np.ndarray:
        """行列演算（Hadamard積 + SHA計算）"""
        
        # 要素ごとの積
        hadamard_product = seed_vector * master_vector
        
        # SHA-256で追加のランダム性を付与
        product_bytes = hadamard_product.astype(np.uint8).tobytes()
        hash_result = hashlib.sha256(product_bytes).digest()
        
        # ベクトルに変換
        result = np.frombuffer(hash_result, dtype=np.uint8).astype(np.float64)
        
        return result
    
    def authenticate_multi_layer(self, 
                                context: AuthenticationContext) -> Dict[str, bytes]:
        """多層認証キー導出"""
        
        auth_keys = {}
        
        # Device層
        device_seed_vec = self.seed_to_vector(context.device_seed)
        device_master_vec = self.seed_to_vector(
            'base64:' + base64.b64encode(self.master_keys['device']).decode(),
            len(device_seed_vec)
        )
        device_auth_vec = self.matrix_multiply(device_seed_vec, device_master_vec)
        context.device_auth_key = self.vector_to_key(device_auth_vec)
        auth_keys['device'] = context.device_auth_key
        
        # OS層
        os_seed_vec = self.seed_to_vector(context.os_seed)
        os_master_vec = self.seed_to_vector(
            'base64:' + base64.b64encode(self.master_keys['os']).decode(),
            len(os_seed_vec)
        )
        os_auth_vec = self.matrix_multiply(os_seed_vec, os_master_vec)
        context.os_auth_key = self.vector_to_key(os_auth_vec)
        auth_keys['os'] = context.os_auth_key
        
        # Application層
        app_seed_vec = self.seed_to_vector(context.app_seed)
        app_master_vec = self.seed_to_vector(
            'base64:' + base64.b64encode(self.master_keys['application']).decode(),
            len(app_seed_vec)
        )
        app_auth_vec = self.matrix_multiply(app_seed_vec, app_master_vec)
        context.app_auth_key = self.vector_to_key(app_auth_vec)
        auth_keys['application'] = context.app_auth_key
        
        return auth_keys
    
    def verify_auth_keys(self, auth_keys: Dict[str, bytes]) -> bool:
        """認証キーの妥当性チェック"""
        
        for layer, key in auth_keys.items():
            if not isinstance(key, bytes) or len(key) < 16:
                return False
        
        return True


class SemiCompilingParser:
    """セミコンパイリングパーサー"""
    
    def __init__(self, spec_db: Dict):
        self.spec_db = spec_db
        self.instructions_map = {
            spec['mnemonic']: instr_id 
            for instr_id, spec in spec_db['instructions'].items()
        }
        self.tokens = []
    
    def tokenize(self, source_code: str) -> List[TokenInfo]:
        """ソースコードをトークン化"""
        
        tokens = []
        lines = source_code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # コメント除去
            if '#' in line:
                line = line[:line.index('#')]
            
            line = line.strip()
            if not line:
                continue
            
            # 簡易パーサー（トークン分割）
            token_pattern = r'([A-Z_]+)\s*\((.*?)\)'
            matches = re.finditer(token_pattern, line)
            
            col = 0
            for match in matches:
                mnemonic = match.group(1)
                args_str = match.group(2)
                
                if mnemonic not in self.instructions_map:
                    raise SyntaxError(f"Unknown instruction: {mnemonic} at line {line_num}")
                
                instr_id = self.instructions_map[mnemonic]
                args = self._parse_args(args_str)
                
                token = TokenInfo(
                    instruction_id=instr_id,
                    mnemonic=mnemonic,
                    args=args,
                    line=line_num,
                    column=col
                )
                tokens.append(token)
                col = match.end()
        
        self.tokens = tokens
        return tokens
    
    def _parse_args(self, args_str: str) -> List[Any]:
        """引数文字列をパース"""
        
        if not args_str.strip():
            return []
        
        args = []
        # 簡易的な引数パーサー
        for arg in args_str.split(','):
            arg = arg.strip()
            
            # 数値
            if arg.isdigit():
                args.append(int(arg))
            # 浮動小数点数
            elif re.match(r'^\d+\.\d+$', arg):
                args.append(float(arg))
            # 文字列（クォート）
            elif arg.startswith('"') and arg.endswith('"'):
                args.append(arg[1:-1])
            # 変数名
            else:
                args.append(arg)
        
        return args
    
    def validate_tokens(self, tokens: List[TokenInfo], 
                       auth_keys: Dict[str, bytes]) -> bool:
        """トークンの妥当性検証"""
        
        for token in tokens:
            spec = self.spec_db['instructions'].get(token.instruction_id)
            
            if not spec:
                raise ValueError(f"Unknown instruction ID: {token.instruction_id}")
            
            # 引数個数チェック
            required_args = sum(1 for arg in spec['args'] if arg.get('required', False))
            if len(token.args) < required_args:
                raise ValueError(
                    f"Instruction {spec['mnemonic']} requires at least {required_args} arguments "
                    f"at line {token.line}"
                )
            
            # 引数型チェック
            for i, (arg, arg_spec) in enumerate(zip(token.args, spec['args'])):
                allowed_types = arg_spec.get('allowed_types', [])
                arg_type = self._infer_type(arg)
                
                if arg_type not in allowed_types:
                    raise TypeError(
                        f"Argument {i} type mismatch: expected {allowed_types}, got {arg_type} "
                        f"at line {token.line}"
                    )
        
        return True
    
    def _infer_type(self, arg: Any) -> str:
        """引数の型を推論"""
        
        if isinstance(arg, bool):
            return 'bool'
        elif isinstance(arg, int):
            return 'int'
        elif isinstance(arg, float):
            return 'float'
        elif isinstance(arg, str):
            if arg.startswith('{') and arg.endswith('}'):
                return 'block'
            # ブロック参照文字列もblockとして扱う
            if arg.startswith('block') or arg.startswith('args'):
                return 'block'
            return 'string'
        else:
            return 'unknown'
    
    def construct_ast(self, tokens: List[TokenInfo]) -> ASTNode:
        """トークンからAST（抽象構文木）を構成"""
        
        root = ASTNode(
            node_type='program',
            semantic_name='root_program',
            instruction_id=0,
            args=[],
            children=[],
            security_level='HIGH'
        )
        
        for token in tokens:
            spec = self.spec_db['instructions'][token.instruction_id]
            
            node = ASTNode(
                node_type=spec['node_type'],
                semantic_name=spec['semantic_name'],
                instruction_id=token.instruction_id,
                args=token.args,
                children=[],
                security_level=spec['security_level']
            )
            
            root.children.append(node)
        
        return root


class MatrixAuthenticatedCompiler:
    """セミコンパイル + 行列認証コンパイラ"""
    
    def __init__(self, spec_db: Dict, master_keys: Dict[str, str]):
        self.spec_db = spec_db
        self.authenticator = MatrixAuthenticator(master_keys)
        self.parser = SemiCompilingParser(spec_db)
        self.compilation_log = []
    
    def compile(self, source_code: str,
               context: AuthenticationContext) -> Tuple[bytes, Dict[str, Any]]:
        """
        ソースコードをコンパイル
        
        Returns:
            (bytecode, metadata)
        """
        
        compilation_metadata = {
            'source_hash': hashlib.sha256(source_code.encode()).hexdigest(),
            'timestamp': datetime.now().isoformat(),
            'auth_context': asdict(context),
            'compilation_steps': [],
            'status': 'success'
        }
        
        try:
            # Step 1: 多層認証
            self._log("Step 1: Multi-layer authentication", compilation_metadata)
            auth_keys = self.authenticator.authenticate_multi_layer(context)
            
            if not self.authenticator.verify_auth_keys(auth_keys):
                raise ValueError("Authentication keys verification failed")
            
            self._log("Authentication successful", compilation_metadata)
            
            # Step 2: トークン化
            self._log("Step 2: Tokenization", compilation_metadata)
            tokens = self.parser.tokenize(source_code)
            
            self._log(f"Tokenized {len(tokens)} instructions", compilation_metadata)
            
            # Step 3: トークン検証
            self._log("Step 3: Token validation", compilation_metadata)
            self.parser.validate_tokens(tokens, auth_keys)
            
            self._log("Token validation passed", compilation_metadata)
            
            # Step 4: AST動的再構成
            self._log("Step 4: AST reconstruction", compilation_metadata)
            ast = self.parser.construct_ast(tokens)
            
            self._log(f"AST constructed with {len(ast.children)} nodes", compilation_metadata)
            
            # Step 5: セキュリティレベル検証
            self._log("Step 5: Security level verification", compilation_metadata)
            self._verify_security_levels(ast, context)
            
            self._log("Security verification passed", compilation_metadata)
            
            # Step 6: バイトコード生成
            self._log("Step 6: Bytecode generation", compilation_metadata)
            bytecode = self._generate_bytecode(ast, auth_keys)
            
            self._log(f"Generated {len(bytecode)} bytes of bytecode", compilation_metadata)
            
            # Step 7: 署名
            self._log("Step 7: Code signing", compilation_metadata)
            signed_bytecode = self._sign_bytecode(bytecode, auth_keys)
            
            return signed_bytecode, compilation_metadata
        
        except Exception as e:
            compilation_metadata['status'] = 'error'
            compilation_metadata['error'] = str(e)
            self._log(f"Compilation error: {e}", compilation_metadata)
            raise
    
    def _verify_security_levels(self, ast: ASTNode, 
                               context: AuthenticationContext) -> bool:
        """セキュリティレベル検証"""
        
        def check_node(node: ASTNode):
            # 高いセキュリティレベルの命令は高いセキュリティコンテキストが必要
            if node.security_level == 'HIGH':
                # デバイス認証が必要
                if not context.device_auth_key:
                    raise PermissionError(
                        f"High security instruction {node.semantic_name} requires device authentication"
                    )
            
            for child in node.children:
                check_node(child)
        
        check_node(ast)
        return True
    
    def _generate_bytecode(self, ast: ASTNode, auth_keys: Dict[str, bytes]) -> bytes:
        """バイトコード生成"""
        
        bytecode = bytearray()
        
        # ヘッダー
        bytecode.extend(b'HIRAGANA_BYTECODE_V1')
        
        # メタデータ
        metadata = json.dumps({
            'num_instructions': len(ast.children),
            'security_level': ast.security_level
        }).encode()
        bytecode.extend(struct.pack('>H', len(metadata)))
        bytecode.extend(metadata)
        
        # 命令セット
        for instruction in ast.children:
            bytecode.extend(struct.pack('B', instruction.instruction_id))
            
            # 引数エンコード
            args_encoded = json.dumps(instruction.args).encode()
            bytecode.extend(struct.pack('>H', len(args_encoded)))
            bytecode.extend(args_encoded)
        
        return bytes(bytecode)
    
    def _sign_bytecode(self, bytecode: bytes, 
                      auth_keys: Dict[str, bytes]) -> bytes:
        """バイトコード署名"""
        
        # 簡易署名（実運用ではEd25519など使用）
        signature_data = bytecode + auth_keys['device'] + auth_keys['os']
        signature = hashlib.sha256(signature_data).digest()
        
        # 署名付きバイトコード
        signed = bytearray()
        signed.extend(b'SIGNED\x00\x01')
        signed.extend(struct.pack('>H', len(signature)))
        signed.extend(signature)
        signed.extend(bytecode)
        
        return bytes(signed)
    
    def _log(self, message: str, metadata: Dict):
        """コンパイルログ記録"""
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'message': message
        }
        metadata['compilation_steps'].append(log_entry)
        self.compilation_log.append(message)
    
    def get_compilation_report(self) -> str:
        """コンパイル報告書"""
        
        report = "=" * 60 + "\n"
        report += "COMPILATION REPORT\n"
        report += "=" * 60 + "\n"
        
        for step in self.compilation_log:
            report += f"  → {step}\n"
        
        report += "=" * 60 + "\n"
        return report


# ============================================================================
# サンプル実行
# ============================================================================

def main():
    """サンプル実行"""
    
    print("=" * 70)
    print("Matrix Authenticated Compiler - Sample Execution")
    print("=" * 70)
    print()
    
    # Step 1: ビルドタイム - バイナリDB構築
    print("[BUILD TIME] Creating Binary Database...")
    print("-" * 70)
    
    db_builder = BinaryDatabaseBuilder()
    spec_db = db_builder.build_default_spec()
    
    print(f"✓ Instructions defined: {len(spec_db['instructions'])}")
    for instr_id, spec in spec_db['instructions'].items():
        print(f"  0x{instr_id:02X}: {spec['mnemonic']:10s} ({spec['semantic_name']})")
    
    print()
    
    # Step 2: ランタイム - マスターキー定義
    print("[RUNTIME] Setting up Master Keys...")
    print("-" * 70)
    
    # デモ用の簡易マスターキー（本運用ではセキュアに管理）
    master_keys = {
        'device': f"base64:{base64.b64encode(b'device_master_key_12345678901234').decode()}",
        'os': f"base64:{base64.b64encode(b'os_master_key_1234567890123456789').decode()}",
        'application': f"base64:{base64.b64encode(b'app_master_key_123456789012345678').decode()}"
    }
    
    print("✓ Master keys configured for 3 layers (device, os, application)")
    print()
    
    # Step 3: 認証コンテキスト構築
    print("[AUTHENTICATION] Building Authentication Context...")
    print("-" * 70)
    
    # デモ用シード値
    context = AuthenticationContext(
        device_seed=f"base64:{base64.b64encode(b'device_seed_001_test_hiragana').decode()}",
        os_seed=f"base64:{base64.b64encode(b'linux_kernel_5_10_seed_hiragana').decode()}",
        app_seed=f"base64:{base64.b64encode(b'application_v1_0_0_seed_hiragana').decode()}"
    )
    
    print(f"✓ Device seed: {context.device_seed[:30]}...")
    print(f"✓ OS seed:     {context.os_seed[:30]}...")
    print(f"✓ App seed:    {context.app_seed[:30]}...")
    print()
    
    # Step 4: コンパイラ初期化
    print("[COMPILER] Initializing Compiler...")
    print("-" * 70)
    
    compiler = MatrixAuthenticatedCompiler(spec_db, master_keys)
    
    print("✓ Compiler initialized with authenticated matrix engine")
    print()
    
    # Step 5: ソースコード定義
    print("[SOURCE CODE] Sample Hiragana Program...")
    print("-" * 70)
    
    sample_source = """
    # Sample Hiragana Program
    ASSIGN("x", 10)
    ASSIGN("y", 20)
    IF(1, "block1")
    LOOP(5, "block2")
    PRINT("Processing...")
    CALL("function1", "args1")
    PRINT("Complete")
    """
    
    print(sample_source)
    print()
    
    # Step 6: コンパイル実行
    print("[COMPILATION] Compiling with Matrix Authentication...")
    print("-" * 70)
    
    try:
        bytecode, metadata = compiler.compile(sample_source, context)
        
        print(compiler.get_compilation_report())
        
        print("[RESULT] Compilation Successful!")
        print(f"✓ Bytecode size: {len(bytecode)} bytes")
        print(f"✓ Source hash: {metadata['source_hash'][:16]}...")
        print(f"✓ Auth layers passed: device, os, application")
        print()
        
        # Step 7: メタデータ表示
        print("[METADATA] Compilation Metadata...")
        print("-" * 70)
        
        print(json.dumps({
            'source_hash': metadata['source_hash'],
            'timestamp': metadata['timestamp'],
            'status': metadata['status'],
            'steps': len(metadata['compilation_steps'])
        }, indent=2))
        
        print()
        print("=" * 70)
        print("✓ All layers authenticated successfully!")
        print("✓ Code is ready for secure execution")
        print("=" * 70)
        
    except Exception as e:
        print(f"✗ Compilation failed: {e}")
        print()
        print(compiler.get_compilation_report())


if __name__ == "__main__":
    main()
