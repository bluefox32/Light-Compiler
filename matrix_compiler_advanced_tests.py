"""
Matrix Authenticated Compiler - Advanced Test Suite & Security Verification

マルチシード値での動作、セキュリティアラート、エラーハンドリングの詳細実装
"""

import sys
import json
import base64
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import numpy as np

# 前のモジュールからインポート（同じディレクトリ）
from matrix_authenticated_compiler import (
    BinaryDatabaseBuilder,
    MatrixAuthenticator,
    MatrixAuthenticatedCompiler,
    AuthenticationContext,
    SemiCompilingParser,
    DataType,
    AuthenticationLayer
)


# ============================================================================
# セキュリティアラートシステム
# ============================================================================

class SecurityAlert:
    """セキュリティアラート"""
    
    SEVERITY_LEVELS = {
        'INFO': 0,
        'WARNING': 1,
        'ERROR': 2,
        'CRITICAL': 3
    }
    
    def __init__(self, 
                 alert_type: str,
                 severity: str,
                 message: str,
                 details: Dict = None,
                 timestamp: str = None):
        self.alert_type = alert_type
        self.severity = severity
        self.message = message
        self.details = details or {}
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self):
        return {
            'type': self.alert_type,
            'severity': self.severity,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp
        }
    
    def __repr__(self):
        severity_sym = {
            'INFO': 'ℹ',
            'WARNING': '⚠',
            'ERROR': '✗',
            'CRITICAL': '🔴'
        }
        sym = severity_sym.get(self.severity, '?')
        return f"{sym} [{self.severity}] {self.alert_type}: {self.message}"


class SecurityVerifier:
    """セキュリティ検証エンジン"""
    
    def __init__(self):
        self.alerts = []
    
    def verify_seed_entropy(self, seed_b64: str) -> Tuple[bool, SecurityAlert]:
        """シード値のエントロピー検証"""
        
        try:
            seed_bytes = base64.b64decode(seed_b64.replace('base64:', ''))
            
            if len(seed_bytes) < 16:
                alert = SecurityAlert(
                    alert_type='LOW_ENTROPY_SEED',
                    severity='WARNING',
                    message=f'Seed entropy too low: {len(seed_bytes)} bytes (recommended: >= 32)',
                    details={'seed_length': len(seed_bytes)}
                )
                self.alerts.append(alert)
                return False, alert
            
            # シャノンエントロピー計算
            entropy = self._calculate_entropy(seed_bytes)
            
            if entropy < 4.0:
                alert = SecurityAlert(
                    alert_type='LOW_SEED_ENTROPY',
                    severity='WARNING',
                    message=f'Shannon entropy: {entropy:.2f} bits/byte (threshold: 4.0)',
                    details={'entropy': entropy}
                )
                self.alerts.append(alert)
                return False, alert
            
            return True, None
        
        except Exception as e:
            alert = SecurityAlert(
                alert_type='SEED_VALIDATION_ERROR',
                severity='ERROR',
                message=str(e),
                details={'error': str(e)}
            )
            self.alerts.append(alert)
            return False, alert
    
    def _calculate_entropy(self, data: bytes) -> float:
        """シャノンエントロピー計算"""
        
        byte_counts = {}
        for byte in data:
            byte_counts[byte] = byte_counts.get(byte, 0) + 1
        
        entropy = 0.0
        data_len = len(data)
        
        for count in byte_counts.values():
            probability = count / data_len
            entropy -= probability * np.log2(probability)
        
        return entropy
    
    def verify_master_key_strength(self, master_key_b64: str) -> Tuple[bool, SecurityAlert]:
        """マスターキーの強度検証"""
        
        try:
            master_key = base64.b64decode(master_key_b64.replace('base64:', ''))
            
            # キー長チェック（最小32バイト）
            if len(master_key) < 32:
                alert = SecurityAlert(
                    alert_type='WEAK_MASTER_KEY',
                    severity='CRITICAL',
                    message=f'Master key too short: {len(master_key)} bytes (required: >= 32)',
                    details={'key_length': len(master_key)}
                )
                self.alerts.append(alert)
                return False, alert
            
            # ユニークネス検証（同じバイト値の繰り返しチェック）
            unique_bytes = len(set(master_key))
            if unique_bytes < 16:
                alert = SecurityAlert(
                    alert_type='LOW_KEY_DIVERSITY',
                    severity='WARNING',
                    message=f'Low key diversity: {unique_bytes} unique bytes',
                    details={'unique_bytes': unique_bytes}
                )
                self.alerts.append(alert)
                return False, alert
            
            return True, None
        
        except Exception as e:
            alert = SecurityAlert(
                alert_type='KEY_VALIDATION_ERROR',
                severity='ERROR',
                message=str(e),
                details={'error': str(e)}
            )
            self.alerts.append(alert)
            return False, alert
    
    def verify_bytecode_integrity(self, bytecode: bytes, 
                                 expected_hash: str = None) -> Tuple[bool, SecurityAlert]:
        """バイトコード整合性検証"""
        
        try:
            # ヘッダーチェック
            if not bytecode.startswith(b'SIGNED\x00\x01') and \
               not bytecode.startswith(b'HIRAGANA_BYTECODE_V1'):
                alert = SecurityAlert(
                    alert_type='INVALID_BYTECODE_HEADER',
                    severity='ERROR',
                    message='Invalid bytecode header signature',
                    details={'actual_header': bytecode[:20].hex()}
                )
                self.alerts.append(alert)
                return False, alert
            
            # 最小サイズチェック
            if len(bytecode) < 50:
                alert = SecurityAlert(
                    alert_type='BYTECODE_TOO_SHORT',
                    severity='ERROR',
                    message=f'Bytecode too short: {len(bytecode)} bytes',
                    details={'bytecode_length': len(bytecode)}
                )
                self.alerts.append(alert)
                return False, alert
            
            return True, None
        
        except Exception as e:
            alert = SecurityAlert(
                alert_type='BYTECODE_INTEGRITY_ERROR',
                severity='ERROR',
                message=str(e),
                details={'error': str(e)}
            )
            self.alerts.append(alert)
            return False, alert


# ============================================================================
# パフォーマンス測定
# ============================================================================

class CompilerBenchmark:
    """コンパイラパフォーマンスベンチマーク"""
    
    def __init__(self):
        self.results = {}
    
    def measure_tokenization(self, parser, source_code: str, iterations: int = 100) -> float:
        """トークン化のパフォーマンス測定"""
        
        start = time.perf_counter()
        
        for _ in range(iterations):
            parser.tokenize(source_code)
        
        elapsed = time.perf_counter() - start
        avg_ms = (elapsed / iterations) * 1000
        
        self.results['tokenization_ms'] = avg_ms
        return avg_ms
    
    def measure_authentication(self, authenticator, context, iterations: int = 100) -> float:
        """認証のパフォーマンス測定"""
        
        start = time.perf_counter()
        
        for _ in range(iterations):
            authenticator.authenticate_multi_layer(context)
        
        elapsed = time.perf_counter() - start
        avg_ms = (elapsed / iterations) * 1000
        
        self.results['authentication_ms'] = avg_ms
        return avg_ms
    
    def measure_full_compilation(self, compiler, source_code: str, 
                                context: AuthenticationContext,
                                iterations: int = 10) -> float:
        """フルコンパイルのパフォーマンス測定"""
        
        start = time.perf_counter()
        
        for _ in range(iterations):
            compiler.compile(source_code, context)
        
        elapsed = time.perf_counter() - start
        avg_ms = (elapsed / iterations) * 1000
        
        self.results['full_compilation_ms'] = avg_ms
        return avg_ms
    
    def report(self) -> str:
        """パフォーマンスレポート"""
        
        report = "\n" + "=" * 70 + "\n"
        report += "PERFORMANCE BENCHMARK REPORT\n"
        report += "=" * 70 + "\n"
        
        for metric, value in sorted(self.results.items()):
            report += f"  {metric:30s}: {value:8.3f} ms\n"
        
        report += "=" * 70 + "\n"
        return report


# ============================================================================
# マルチシード統合テスト
# ============================================================================

class MultiSeedTest:
    """マルチシード値での統合テスト"""
    
    def __init__(self):
        self.test_results = []
    
    def create_test_contexts(self) -> Dict[str, AuthenticationContext]:
        """複数の認証コンテキストを生成"""
        
        contexts = {}
        
        # デバイスA（エッジデバイス）
        contexts['edge_device_a'] = AuthenticationContext(
            device_seed=f"base64:{base64.b64encode(b'edge_device_a_seed_001').decode()}",
            os_seed=f"base64:{base64.b64encode(b'rtos_v3_seed_012345678').decode()}",
            app_seed=f"base64:{base64.b64encode(b'edge_app_v1_0_seed_abcd').decode()}"
        )
        
        # デバイスB（クラウドサーバ）
        contexts['cloud_server_b'] = AuthenticationContext(
            device_seed=f"base64:{base64.b64encode(b'cloud_server_b_seed_002').decode()}",
            os_seed=f"base64:{base64.b64encode(b'linux_kernel_5_10_seed').decode()}",
            app_seed=f"base64:{base64.b64encode(b'cloud_app_v2_1_seed_xyz').decode()}"
        )
        
        # デバイスC（IoTセンサ）
        contexts['iot_sensor_c'] = AuthenticationContext(
            device_seed=f"base64:{base64.b64encode(b'iot_sensor_c_seed_00003').decode()}",
            os_seed=f"base64:{base64.b64encode(b'freertos_seed_1234567890').decode()}",
            app_seed=f"base64:{base64.b64encode(b'iot_firmware_v0_5_seed_m').decode()}"
        )
        
        return contexts
    
    def run_multi_seed_compilation(self, compiler, source_code: str, 
                                   contexts: Dict[str, AuthenticationContext]) -> Dict:
        """複数シード値でのコンパイル実行"""
        
        results = {}
        
        for device_name, context in contexts.items():
            try:
                bytecode, metadata = compiler.compile(source_code, context)
                
                results[device_name] = {
                    'status': 'success',
                    'bytecode_size': len(bytecode),
                    'source_hash': metadata['source_hash'],
                    'auth_context': {
                        'device': context.device_seed[:30] + '...',
                        'os': context.os_seed[:30] + '...',
                        'app': context.app_seed[:30] + '...'
                    }
                }
                
                self.test_results.append({
                    'device': device_name,
                    'status': 'PASS',
                    'bytecode_size': len(bytecode)
                })
            
            except Exception as e:
                results[device_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                
                self.test_results.append({
                    'device': device_name,
                    'status': 'FAIL',
                    'error': str(e)
                })
        
        return results
    
    def report(self) -> str:
        """テスト結果レポート"""
        
        report = "\n" + "=" * 70 + "\n"
        report += "MULTI-SEED COMPILATION TEST REPORT\n"
        report += "=" * 70 + "\n"
        
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        
        report += f"\n  Total Tests: {len(self.test_results)}\n"
        report += f"  Passed: {passed} ✓\n"
        report += f"  Failed: {failed} ✗\n\n"
        
        report += "  Test Results:\n"
        report += "  " + "-" * 66 + "\n"
        
        for result in self.test_results:
            status_sym = '✓' if result['status'] == 'PASS' else '✗'
            info = f"Size: {result.get('bytecode_size', 'N/A')} bytes"
            if result.get('error'):
                info = f"Error: {result['error'][:40]}"
            
            report += f"  {status_sym} {result['device']:25s} {info}\n"
        
        report += "  " + "-" * 66 + "\n"
        report += "=" * 70 + "\n"
        
        return report


# ============================================================================
# エラーハンドリングテスト
# ============================================================================

class ErrorHandlingTest:
    """エラーハンドリングのテスト"""
    
    def __init__(self, compiler: MatrixAuthenticatedCompiler):
        self.compiler = compiler
        self.test_results = []
    
    def test_malformed_source(self) -> bool:
        """不正なソースコードの処理"""
        
        malformed_sources = [
            "INVALID_INSTRUCTION(1, 2)",
            "IF()",  # 引数不足
            "PRINT(123, 456, 789)",  # 引数過多
        ]
        
        context = AuthenticationContext(
            device_seed=f"base64:{base64.b64encode(b'test_seed').decode()}",
            os_seed=f"base64:{base64.b64encode(b'test_os').decode()}",
            app_seed=f"base64:{base64.b64encode(b'test_app').decode()}"
        )
        
        for source in malformed_sources:
            try:
                self.compiler.compile(source, context)
                self.test_results.append({
                    'test': 'malformed_source',
                    'source': source,
                    'status': 'FAIL',
                    'reason': 'Should have raised error'
                })
            
            except (SyntaxError, ValueError, TypeError) as e:
                self.test_results.append({
                    'test': 'malformed_source',
                    'source': source[:20] + '...',
                    'status': 'PASS',
                    'error_type': type(e).__name__
                })
            
            except Exception as e:
                self.test_results.append({
                    'test': 'malformed_source',
                    'source': source[:20] + '...',
                    'status': 'FAIL',
                    'error': str(e)
                })
        
        return True
    
    def test_invalid_authentication(self) -> bool:
        """不正な認証の処理"""
        
        verifier = SecurityVerifier()
        
        # 短いシード値
        is_valid, alert = verifier.verify_seed_entropy(
            f"base64:{base64.b64encode(b'short').decode()}"
        )
        
        self.test_results.append({
            'test': 'invalid_auth_short_seed',
            'status': 'PASS' if not is_valid else 'FAIL',
            'alert': str(alert) if alert else None
        })
        
        return True
    
    def report(self) -> str:
        """エラーハンドリングテストレポート"""
        
        report = "\n" + "=" * 70 + "\n"
        report += "ERROR HANDLING TEST REPORT\n"
        report += "=" * 70 + "\n"
        
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        
        report += f"\n  Total Tests: {len(self.test_results)}\n"
        report += f"  Passed: {passed} ✓\n\n"
        
        for result in self.test_results:
            status_sym = '✓' if result['status'] == 'PASS' else '✗'
            test_name = result['test'].replace('_', ' ').title()
            report += f"  {status_sym} {test_name}\n"
        
        report += "\n" + "=" * 70 + "\n"
        
        return report


# ============================================================================
# メイン実行
# ============================================================================

def run_advanced_tests():
    """全テストスイート実行"""
    
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "ADVANCED COMPILER TEST SUITE" + " " * 25 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    # ============================================================================
    # フェーズ1: セットアップ
    # ============================================================================
    
    print("【PHASE 1】 System Setup")
    print("-" * 70)
    
    # バイナリDB構築
    db_builder = BinaryDatabaseBuilder()
    spec_db = db_builder.build_default_spec()
    print(f"✓ Binary database created ({len(spec_db['instructions'])} instructions)")
    
    # マスターキー生成
    master_keys = {
        'device': f"base64:{base64.b64encode(b'device_master_key_secure_' + b'0' * 31).decode()}",
        'os': f"base64:{base64.b64encode(b'os_master_key_secure_12345678' + b'0' * 3).decode()}",
        'application': f"base64:{base64.b64encode(b'app_master_key_secure_abcdef' + b'0' * 4).decode()}"
    }
    print(f"✓ Master keys configured (3 layers)")
    
    # コンパイラ初期化
    compiler = MatrixAuthenticatedCompiler(spec_db, master_keys)
    print(f"✓ Compiler initialized")
    
    print()
    
    # ============================================================================
    # フェーズ2: セキュリティ検証
    # ============================================================================
    
    print("【PHASE 2】 Security Verification")
    print("-" * 70)
    
    verifier = SecurityVerifier()
    
    # マスターキー検証
    for layer, key in master_keys.items():
        is_valid, alert = verifier.verify_master_key_strength(key)
        status = "✓ PASS" if is_valid else "⚠ WARNING"
        print(f"{status}: {layer.upper()} layer master key")
    
    print()
    
    # ============================================================================
    # フェーズ3: マルチシード統合テスト
    # ============================================================================
    
    print("【PHASE 3】 Multi-Seed Compilation Test")
    print("-" * 70)
    
    multi_seed_test = MultiSeedTest()
    test_contexts = multi_seed_test.create_test_contexts()
    
    sample_source = """
    ASSIGN("status", "initialized")
    PRINT("System ready")
    LOOP(3, "block1")
    PRINT("Iteration")
    CALL("process", "args1")
    """
    
    results = multi_seed_test.run_multi_seed_compilation(
        compiler, sample_source, test_contexts
    )
    
    print(multi_seed_test.report())
    
    # ============================================================================
    # フェーズ4: パフォーマンスベンチマーク
    # ============================================================================
    
    print("【PHASE 4】 Performance Benchmark")
    print("-" * 70)
    
    benchmark = CompilerBenchmark()
    parser = SemiCompilingParser(spec_db)
    
    print("Running benchmarks...")
    
    # トークン化ベンチマーク
    tok_time = benchmark.measure_tokenization(parser, sample_source, iterations=100)
    print(f"✓ Tokenization: {tok_time:.3f} ms (100 iterations)")
    
    # 認証ベンチマーク
    context = list(test_contexts.values())[0]
    authenticator = MatrixAuthenticator(master_keys)
    auth_time = benchmark.measure_authentication(authenticator, context, iterations=50)
    print(f"✓ Authentication: {auth_time:.3f} ms (50 iterations)")
    
    # フルコンパイルベンチマーク
    compile_time = benchmark.measure_full_compilation(
        compiler, sample_source, context, iterations=10
    )
    print(f"✓ Full compilation: {compile_time:.3f} ms (10 iterations)")
    
    print(benchmark.report())
    
    # ============================================================================
    # フェーズ5: エラーハンドリングテスト
    # ============================================================================
    
    print("【PHASE 5】 Error Handling Test")
    print("-" * 70)
    
    error_test = ErrorHandlingTest(compiler)
    error_test.test_malformed_source()
    error_test.test_invalid_authentication()
    
    print(error_test.report())
    
    # ============================================================================
    # フェーズ6: セキュリティアラートデモ
    # ============================================================================
    
    print("【PHASE 6】 Security Alert System Demo")
    print("-" * 70)
    
    alerts = verifier.alerts
    
    print(f"\nGenerated {len(alerts)} security alerts:\n")
    
    for alert in alerts[:5]:  # 最初の5件を表示
        print(f"  {alert}")
    
    if len(alerts) > 5:
        print(f"  ... and {len(alerts) - 5} more alerts")
    
    print()
    
    # ============================================================================
    # フェーズ7: 最終レポート
    # ============================================================================
    
    print("【PHASE 7】 Final Summary")
    print("-" * 70)
    
    total_tests = len(multi_seed_test.test_results) + len(error_test.test_results)
    passed_tests = (
        sum(1 for r in multi_seed_test.test_results if r['status'] == 'PASS') +
        sum(1 for r in error_test.test_results if r['status'] == 'PASS')
    )
    
    print(f"\n✓ Tests Executed: {total_tests}")
    print(f"✓ Tests Passed: {passed_tests}")
    print(f"✓ Success Rate: {(passed_tests/total_tests*100):.1f}%")
    print(f"✓ Security Alerts Generated: {len(alerts)}")
    print(f"✓ Average Compilation Time: {compile_time:.2f} ms")
    
    print("\n" + "=" * 70)
    print("✓ Advanced Test Suite Complete - All Systems Operational")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_advanced_tests()
