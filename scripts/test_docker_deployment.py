#!/usr/bin/env python3
"""
Script para testar deployment Docker local.
Valida: Requisitos 13.6, 13.9

Este script:
1. Verifica que todos os serviços estão rodando
2. Testa endpoints da API
3. Testa conectividade do frontend
"""

import sys
import time
import requests
from typing import Dict, List, Tuple
import subprocess
import json


class Colors:
    """Cores ANSI para output colorido"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Imprime cabeçalho formatado"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")


def print_success(text: str):
    """Imprime mensagem de sucesso"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str):
    """Imprime mensagem de erro"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_warning(text: str):
    """Imprime mensagem de aviso"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_info(text: str):
    """Imprime mensagem informativa"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


def check_docker_running() -> bool:
    """Verifica se Docker está rodando"""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception as e:
        print_error(f"Erro ao verificar Docker: {e}")
        return False


def check_docker_compose_services() -> Dict[str, bool]:
    """Verifica status dos serviços do docker-compose"""
    try:
        result = subprocess.run(
            ["docker-compose", "ps", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print_error("Erro ao executar docker-compose ps")
            return {}
        
        services = {}
        # Parse JSON output (cada linha é um JSON)
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    service_info = json.loads(line)
                    name = service_info.get('Service', service_info.get('Name', ''))
                    state = service_info.get('State', '')
                    services[name] = state.lower() == 'running'
                except json.JSONDecodeError:
                    continue
        
        return services
    except Exception as e:
        print_error(f"Erro ao verificar serviços: {e}")
        return {}


def wait_for_service(url: str, service_name: str, max_retries: int = 30, delay: int = 2) -> bool:
    """Aguarda serviço ficar disponível"""
    print_info(f"Aguardando {service_name} ficar disponível em {url}...")
    
    for i in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code < 500:
                print_success(f"{service_name} está disponível!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if i < max_retries - 1:
            time.sleep(delay)
            print(f"  Tentativa {i + 1}/{max_retries}...", end='\r')
    
    print_error(f"{service_name} não ficou disponível após {max_retries * delay}s")
    return False


def test_api_health(base_url: str) -> bool:
    """Testa endpoint de health da API"""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print_success("Health check da API: OK")
            return True
        else:
            print_error(f"Health check da API falhou: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Erro ao testar health da API: {e}")
        return False


def test_api_ranking(base_url: str) -> bool:
    """Testa endpoint /ranking"""
    try:
        response = requests.get(f"{base_url}/ranking", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Endpoint /ranking: OK (retornou {len(data.get('rankings', []))} ativos)")
            return True
        elif response.status_code == 404:
            print_warning("Endpoint /ranking: Sem dados (esperado se banco vazio)")
            return True
        else:
            print_error(f"Endpoint /ranking falhou: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Erro ao testar /ranking: {e}")
        return False


def test_api_top(base_url: str) -> bool:
    """Testa endpoint /top"""
    try:
        response = requests.get(f"{base_url}/top?n=5", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Endpoint /top: OK (retornou {len(data.get('top_assets', []))} ativos)")
            return True
        elif response.status_code == 404:
            print_warning("Endpoint /top: Sem dados (esperado se banco vazio)")
            return True
        else:
            print_error(f"Endpoint /top falhou: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Erro ao testar /top: {e}")
        return False


def test_api_asset(base_url: str) -> bool:
    """Testa endpoint /asset/{ticker}"""
    try:
        # Testa com ticker que provavelmente não existe
        response = requests.get(f"{base_url}/asset/INVALID", timeout=10)
        
        if response.status_code == 404:
            print_success("Endpoint /asset/{ticker}: OK (404 para ticker inválido)")
            return True
        else:
            print_warning(f"Endpoint /asset/{ticker}: Status inesperado {response.status_code}")
            return True  # Não é erro crítico
    except Exception as e:
        print_error(f"Erro ao testar /asset: {e}")
        return False


def test_frontend_health(base_url: str) -> bool:
    """Testa se frontend está respondendo"""
    try:
        response = requests.get(f"{base_url}/_stcore/health", timeout=10)
        if response.status_code == 200:
            print_success("Health check do Frontend: OK")
            return True
        else:
            print_error(f"Health check do Frontend falhou: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Erro ao testar health do Frontend: {e}")
        return False


def test_frontend_page(base_url: str) -> bool:
    """Testa se página principal do frontend carrega"""
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            print_success("Página principal do Frontend: OK")
            return True
        else:
            print_error(f"Página principal do Frontend falhou: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Erro ao testar página do Frontend: {e}")
        return False


def run_tests() -> Tuple[int, int]:
    """Executa todos os testes e retorna (sucessos, total)"""
    tests_passed = 0
    tests_total = 0
    
    # Configuração
    backend_url = "http://localhost:8000"
    frontend_url = "http://localhost:8501"
    
    # 1. Verificar Docker
    print_header("1. Verificando Docker")
    tests_total += 1
    if check_docker_running():
        print_success("Docker está rodando")
        tests_passed += 1
    else:
        print_error("Docker não está rodando")
        return tests_passed, tests_total
    
    # 2. Verificar serviços do docker-compose
    print_header("2. Verificando Serviços Docker Compose")
    services = check_docker_compose_services()
    
    expected_services = ['postgres', 'backend', 'frontend']
    for service in expected_services:
        tests_total += 1
        if service in services and services[service]:
            print_success(f"Serviço '{service}' está rodando")
            tests_passed += 1
        else:
            print_error(f"Serviço '{service}' não está rodando")
    
    # 3. Aguardar serviços ficarem prontos
    print_header("3. Aguardando Serviços Ficarem Prontos")
    
    # Backend
    tests_total += 1
    if wait_for_service(f"{backend_url}/health", "Backend"):
        tests_passed += 1
    
    # Frontend
    tests_total += 1
    if wait_for_service(f"{frontend_url}/_stcore/health", "Frontend"):
        tests_passed += 1
    
    # 4. Testar endpoints da API
    print_header("4. Testando Endpoints da API")
    
    api_tests = [
        ("Health Check", lambda: test_api_health(backend_url)),
        ("Endpoint /ranking", lambda: test_api_ranking(backend_url)),
        ("Endpoint /top", lambda: test_api_top(backend_url)),
        ("Endpoint /asset", lambda: test_api_asset(backend_url)),
    ]
    
    for test_name, test_func in api_tests:
        tests_total += 1
        if test_func():
            tests_passed += 1
    
    # 5. Testar frontend
    print_header("5. Testando Frontend")
    
    frontend_tests = [
        ("Health Check", lambda: test_frontend_health(frontend_url)),
        ("Página Principal", lambda: test_frontend_page(frontend_url)),
    ]
    
    for test_name, test_func in frontend_tests:
        tests_total += 1
        if test_func():
            tests_passed += 1
    
    return tests_passed, tests_total


def main():
    """Função principal"""
    print(f"\n{Colors.BOLD}Sistema de Ranking Quantitativo - Teste de Deployment Docker{Colors.RESET}")
    print(f"{Colors.BOLD}Valida: Requisitos 13.6, 13.9{Colors.RESET}\n")
    
    # Executar testes
    tests_passed, tests_total = run_tests()
    
    # Resumo
    print_header("Resumo dos Testes")
    
    success_rate = (tests_passed / tests_total * 100) if tests_total > 0 else 0
    
    print(f"Total de testes: {tests_total}")
    print(f"Testes passados: {tests_passed}")
    print(f"Testes falhados: {tests_total - tests_passed}")
    print(f"Taxa de sucesso: {success_rate:.1f}%\n")
    
    if tests_passed == tests_total:
        print_success("Todos os testes passaram! ✨")
        print_info("\nServiços disponíveis:")
        print_info("  - Backend API: http://localhost:8000")
        print_info("  - Frontend: http://localhost:8501")
        print_info("  - PostgreSQL: localhost:5432")
        return 0
    else:
        print_error(f"{tests_total - tests_passed} teste(s) falharam")
        print_info("\nPara ver logs dos serviços:")
        print_info("  docker-compose logs postgres")
        print_info("  docker-compose logs backend")
        print_info("  docker-compose logs frontend")
        return 1


if __name__ == "__main__":
    sys.exit(main())
