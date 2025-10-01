#!/usr/bin/env python3
"""
Food Recipes - Complete Setup and Launch System
===============================================

This script provides a comprehensive setup and launch system for the Food Recipes project.
It includes dependency installation, system checks, and a GUI interface for running
different phases of the project.

Author: Maroš Bednár
Email: bednarmaros341@gmail.com
AIS ID: 116822
Project: Food Recipes - Recipes IR Pipeline
"""

import os
import sys
import subprocess
import platform
import json
import time
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse

# GUI imports (with fallback)
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("Warning: tkinter not available. Running in CLI mode only.")

class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class FoodRecipesLauncher:
    """Main launcher class for Food Recipes project."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / "venv"
        self.python_executable = self._get_python_executable()
        self.system_info = self._get_system_info()
        self.requirements = self._get_requirements()
        self.project_status = self._check_project_status()
        
    def _get_python_executable(self) -> str:
        """Get the correct Python executable path."""
        if self.venv_path.exists():
            if platform.system() == "Windows":
                return str(self.venv_path / "Scripts" / "python.exe")
            else:
                return str(self.venv_path / "bin" / "python")
        return sys.executable
    
    def _get_system_info(self) -> Dict:
        """Get system information."""
        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'python_version': sys.version,
            'architecture': platform.architecture()[0],
            'processor': platform.processor(),
            'venv_exists': self.venv_path.exists(),
            'project_root': str(self.project_root)
        }
    
    def _get_requirements(self) -> List[str]:
        """Get project requirements."""
        return [
            'requests>=2.25.0',
            'beautifulsoup4>=4.9.0',
            'lxml>=4.6.0',
            'ahocorasick>=2.0.0',
            'tqdm>=4.60.0',
            'pyspark>=3.0.0'  # Optional for Spark jobs
        ]
    
    def _check_project_status(self) -> Dict:
        """Check the current status of the project."""
        status = {
            'phases_completed': [],
            'data_available': {},
            'services_running': {},
            'last_run': None
        }
        
        # Check phase completion
        phase_files = {
            'Phase A (Seeds)': 'data/seed_analysis/recipe_seeds.txt',
            'Phase B (Crawling)': 'data/raw',
            'Phase C (Parsing)': 'data/normalized/recipes.jsonl',
            'Phase D (Indexing)': 'data/index/v1/terms.tsv',
            'Phase E (Entities)': 'data/entities/links.jsonl',
            'Phase F (Wikipedia)': 'data/wikipedia_recipes/wikipedia_recipes.jsonl'
        }
        
        for phase, file_path in phase_files.items():
            if Path(file_path).exists():
                status['phases_completed'].append(phase)
                if file_path.endswith('.jsonl'):
                    try:
                        with open(file_path, 'r') as f:
                            count = sum(1 for _ in f)
                        status['data_available'][phase] = count
                    except:
                        status['data_available'][phase] = 'exists'
                else:
                    status['data_available'][phase] = 'exists'
        
        return status
    
    def print_banner(self):
        """Print the project banner."""
        banner = f"""
{Colors.HEADER}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    🍳 FOOD RECIPES - RECIPES IR PIPELINE 🍳                ║
║                                                                              ║
║  Author: Maroš Bednár                                                       ║
║  Email: bednarmaros341@gmail.com                                            ║
║  AIS ID: 116822                                                             ║
║                                                                              ║
║  Complete Recipe Search Engine with AI-Powered Features                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Colors.ENDC}
"""
        print(banner)
    
    def print_system_info(self):
        """Print system information."""
        print(f"{Colors.OKBLUE}System Information:{Colors.ENDC}")
        print(f"  Platform: {self.system_info['platform']} {self.system_info['platform_version']}")
        print(f"  Python: {self.system_info['python_version'].split()[0]}")
        print(f"  Architecture: {self.system_info['architecture']}")
        print(f"  Virtual Environment: {'✅ Available' if self.system_info['venv_exists'] else '❌ Not Found'}")
        print(f"  Project Root: {self.system_info['project_root']}")
        print()
    
    def print_project_status(self):
        """Print current project status."""
        print(f"{Colors.OKGREEN}Project Status:{Colors.ENDC}")
        
        if self.project_status['phases_completed']:
            print("  Completed Phases:")
            for phase in self.project_status['phases_completed']:
                data_info = self.project_status['data_available'].get(phase, '')
                if isinstance(data_info, int):
                    print(f"    ✅ {phase} ({data_info} items)")
                else:
                    print(f"    ✅ {phase}")
        else:
            print("  No phases completed yet.")
        
        print()
    
    def check_dependencies(self) -> Tuple[bool, List[str]]:
        """Check if all dependencies are installed."""
        missing = []
        
        for req in self.requirements:
            package = req.split('>=')[0]
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing.append(req)
        
        return len(missing) == 0, missing
    
    def install_dependencies(self) -> bool:
        """Install missing dependencies."""
        print(f"{Colors.WARNING}Installing dependencies...{Colors.ENDC}")
        
        try:
            # Upgrade pip first
            subprocess.run([self.python_executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                         check=True, capture_output=True)
            
            # Install requirements
            for req in self.requirements:
                print(f"  Installing {req}...")
                subprocess.run([self.python_executable, '-m', 'pip', 'install', req], 
                             check=True, capture_output=True)
            
            print(f"{Colors.OKGREEN}✅ All dependencies installed successfully!{Colors.ENDC}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.FAIL}❌ Failed to install dependencies: {e}{Colors.ENDC}")
            return False
    
    def run_phase(self, phase: str) -> bool:
        """Run a specific phase of the project."""
        phase_commands = {
            'Phase A (Seeds)': [
                'python -m crawler.run --phase seeds --out data/seed_analysis --qps 0.5'
            ],
            'Phase B (Crawling)': [
                'python -m crawler.run --phase crawl --seeds data/seed_analysis/recipe_seeds.txt --out data/raw --limit 1000 --qps 0.3'
            ],
            'Phase C (Parsing)': [
                'python -m parser.run --raw data/raw --out data/normalized/recipes.jsonl'
            ],
            'Phase D (Indexing)': [
                'python -m indexer.run --input data/normalized/recipes.jsonl --out data/index/v1'
            ],
            'Phase E (Entities)': [
                'python -m entities.gazetteer_builder',
                'python -m entities.linker --input data/normalized/recipes.jsonl --gazetteer data/entities/gazetteer_ingredients.tsv --output data/entities/links.jsonl'
            ],
            'Phase F (Wikipedia)': [
                'python run_wikipedia_collection.py --max-recipes 1000 --max-ingredients 500'
            ],
            'Search CLI': [
                'python -m search_cli.run --index data/index/v1 --metric bm25 --q "chicken pasta" --k 10'
            ],
            'Frontend': [
                'python api_server.py &',
                'cd frontend && python -m http.server 3000 &'
            ]
        }
        
        if phase not in phase_commands:
            print(f"{Colors.FAIL}❌ Unknown phase: {phase}{Colors.ENDC}")
            return False
        
        print(f"{Colors.OKBLUE}🚀 Running {phase}...{Colors.ENDC}")
        
        for command in phase_commands[phase]:
            print(f"  Executing: {command}")
            try:
                if '&' in command:
                    # Background process
                    subprocess.Popen(command.replace(' &', ''), shell=True, cwd=self.project_root)
                else:
                    # Foreground process
                    result = subprocess.run(command, shell=True, cwd=self.project_root, 
                                          capture_output=True, text=True)
                    if result.returncode != 0:
                        print(f"{Colors.FAIL}❌ Command failed: {result.stderr}{Colors.ENDC}")
                        return False
            except Exception as e:
                print(f"{Colors.FAIL}❌ Error running command: {e}{Colors.ENDC}")
                return False
        
        print(f"{Colors.OKGREEN}✅ {phase} completed successfully!{Colors.ENDC}")
        return True
    
    def show_menu(self):
        """Show the main menu."""
        while True:
            print(f"\n{Colors.HEADER}Main Menu:{Colors.ENDC}")
            print("1. 📊 Show Project Status")
            print("2. 🔧 Install Dependencies")
            print("3. 🚀 Run Phase A (Seed Extraction)")
            print("4. 🕷️  Run Phase B (Web Crawling)")
            print("5. 📝 Run Phase C (Parsing)")
            print("6. 🔍 Run Phase D (Indexing)")
            print("7. 🏷️  Run Phase E (Entity Linking)")
            print("8. 📚 Run Phase F (Wikipedia Collection)")
            print("9. 🔎 Test Search CLI")
            print("10. 🌐 Launch Frontend")
            print("11. 📈 Run All Phases")
            print("12. 🧹 Clean Project Data")
            print("13. 📖 Show Documentation")
            print("14. 🆘 Help & Troubleshooting")
            print("15. 🚀 Quick Simulation (100 items)")
            print("0. 🚪 Exit")
            
            choice = input(f"\n{Colors.OKCYAN}Enter your choice (0-15): {Colors.ENDC}").strip()
            
            if choice == '0':
                print(f"{Colors.OKGREEN}👋 Goodbye!{Colors.ENDC}")
                break
            elif choice == '1':
                self.print_project_status()
            elif choice == '2':
                self.install_dependencies()
            elif choice == '3':
                self.run_phase('Phase A (Seeds)')
            elif choice == '4':
                self.run_phase('Phase B (Crawling)')
            elif choice == '5':
                self.run_phase('Phase C (Parsing)')
            elif choice == '6':
                self.run_phase('Phase D (Indexing)')
            elif choice == '7':
                self.run_phase('Phase E (Entities)')
            elif choice == '8':
                self.run_phase('Phase F (Wikipedia)')
            elif choice == '9':
                self.run_phase('Search CLI')
            elif choice == '10':
                self.run_phase('Frontend')
            elif choice == '11':
                self.run_all_phases()
            elif choice == '12':
                self.clean_project_data()
            elif choice == '13':
                self.show_documentation()
            elif choice == '14':
                self.show_help()
            elif choice == '15':
                self.run_quick_simulation()
            else:
                print(f"{Colors.WARNING}❌ Invalid choice. Please try again.{Colors.ENDC}")
    
    def run_all_phases(self):
        """Run all phases in sequence."""
        phases = [
            'Phase A (Seeds)',
            'Phase B (Crawling)', 
            'Phase C (Parsing)',
            'Phase D (Indexing)',
            'Phase E (Entities)',
            'Phase F (Wikipedia)'
        ]
        
        print(f"{Colors.HEADER}🚀 Running All Phases{Colors.ENDC}")
        
        for phase in phases:
            if not self.run_phase(phase):
                print(f"{Colors.FAIL}❌ Failed at {phase}. Stopping.{Colors.ENDC}")
                return
        
        print(f"{Colors.OKGREEN}🎉 All phases completed successfully!{Colors.ENDC}")
    
    def clean_project_data(self):
        """Clean project data directories."""
        print(f"{Colors.WARNING}🧹 Cleaning project data...{Colors.ENDC}")
        
        data_dirs = [
            'data/raw',
            'data/normalized',
            'data/index',
            'data/entities',
            'data/wikipedia_recipes',
            'data/seed_analysis'
        ]
        
        for dir_path in data_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists():
                import shutil
                shutil.rmtree(full_path)
                print(f"  Removed: {dir_path}")
        
        print(f"{Colors.OKGREEN}✅ Project data cleaned!{Colors.ENDC}")
    
    def show_documentation(self):
        """Show available documentation."""
        docs = {
            'README.md': 'Main project documentation',
            'WIKIPEDIA_TUTORIAL.md': 'Wikipedia collection tutorial',
            'WIKIPEDIA_COLLECTION_SUMMARY.md': 'Wikipedia collection summary',
            'packaging/run.sh': 'Shell script for running phases'
        }
        
        print(f"{Colors.HEADER}📖 Available Documentation:{Colors.ENDC}")
        for doc, description in docs.items():
            doc_path = self.project_root / doc
            if doc_path.exists():
                print(f"  ✅ {doc}: {description}")
            else:
                print(f"  ❌ {doc}: {description} (not found)")
        
        print(f"\n{Colors.OKCYAN}To view documentation:{Colors.ENDC}")
        print("  cat README.md")
        print("  cat WIKIPEDIA_TUTORIAL.md")
        print("  less WIKIPEDIA_COLLECTION_SUMMARY.md")
    
    def run_quick_simulation(self):
        """Run quick simulation."""
        print(f"{Colors.OKBLUE}🚀 Starting Quick Simulation...{Colors.ENDC}")
        try:
            result = subprocess.run([self.python_executable, "quick_simulation.py", "--items", "100"], 
                                  cwd=self.project_root, check=True)
            if result.returncode == 0:
                print(f"{Colors.OKGREEN}✅ Quick simulation completed successfully!{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}❌ Quick simulation failed!{Colors.ENDC}")
        except subprocess.CalledProcessError as e:
            print(f"{Colors.FAIL}❌ Error running simulation: {e}{Colors.ENDC}")
        except FileNotFoundError:
            print(f"{Colors.FAIL}❌ quick_simulation.py not found!{Colors.ENDC}")

    def show_help(self):
        """Show help and troubleshooting information."""
        help_text = f"""
{Colors.HEADER}🆘 Help & Troubleshooting{Colors.ENDC}

{Colors.OKBLUE}Common Issues:{Colors.ENDC}
1. Virtual Environment Not Found
   Solution: Run 'python -m venv venv' then 'source venv/bin/activate'

2. Dependencies Not Installing
   Solution: Update pip: 'python -m pip install --upgrade pip'

3. Permission Errors
   Solution: Check file permissions and run with appropriate privileges

4. Network Issues
   Solution: Check internet connection and firewall settings

{Colors.OKBLUE}Project Structure:{Colors.ENDC}
├── crawler/          # Web crawling (Phases A & B)
├── parser/           # HTML parsing (Phase C)
├── indexer/          # Search indexing (Phase D)
├── search_cli/       # Search interface (Phase D)
├── entities/         # Entity linking (Phase E)
├── spark_jobs/       # Spark processing (Phase F)
├── frontend/         # Web interface
├── data/             # All project data
└── docs/             # Documentation

{Colors.OKBLUE}Data Flow:{Colors.ENDC}
Phase A: Seed URLs → data/seed_analysis/
Phase B: HTML pages → data/raw/
Phase C: Parsed recipes → data/normalized/
Phase D: Search index → data/index/
Phase E: Entity links → data/entities/
Phase F: Wikipedia data → data/wikipedia_recipes/

{Colors.OKBLUE}Support:{Colors.ENDC}
Email: bednarmaros341@gmail.com
Project: Food Recipes - Recipes IR Pipeline
"""
        print(help_text)

class FoodRecipesGUI:
    """GUI interface for Food Recipes launcher."""
    
    def __init__(self, launcher: FoodRecipesLauncher):
        self.launcher = launcher
        self.root = tk.Tk()
        self.setup_gui()
    
    def setup_gui(self):
        """Setup the GUI interface."""
        self.root.title("Food Recipes - Setup & Launch")
        self.root.geometry("800x600")
        self.root.configure(bg='#f0f0f0')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="🍳 Food Recipes - Recipes IR Pipeline", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # System info frame
        info_frame = ttk.LabelFrame(main_frame, text="System Information", padding="10")
        info_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.info_text = scrolledtext.ScrolledText(info_frame, height=8, width=70)
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.update_system_info()
        
        # Buttons frame
        buttons_frame = ttk.LabelFrame(main_frame, text="Actions", padding="10")
        buttons_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Create buttons
        buttons = [
            ("📊 Project Status", self.show_status),
            ("🔧 Install Dependencies", self.install_deps),
            ("🚀 Phase A (Seeds)", lambda: self.run_phase("Phase A (Seeds)")),
            ("🕷️ Phase B (Crawling)", lambda: self.run_phase("Phase B (Crawling)")),
            ("📝 Phase C (Parsing)", lambda: self.run_phase("Phase C (Parsing)")),
            ("🔍 Phase D (Indexing)", lambda: self.run_phase("Phase D (Indexing)")),
            ("🏷️ Phase E (Entities)", lambda: self.run_phase("Phase E (Entities)")),
            ("📚 Phase F (Wikipedia)", lambda: self.run_phase("Phase F (Wikipedia)")),
            ("🌐 Launch Frontend", lambda: self.run_phase("Frontend")),
            ("📈 Run All Phases", self.run_all_phases),
            ("🧹 Clean Data", self.clean_data),
            ("📖 Documentation", self.show_docs)
        ]
        
        for i, (text, command) in enumerate(buttons):
            row = i // 3
            col = i % 3
            btn = ttk.Button(buttons_frame, text=text, command=command)
            btn.grid(row=row, column=col, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Output frame
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding="10")
        output_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=15, width=70)
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
    
    def update_system_info(self):
        """Update system information display."""
        info = f"""Platform: {self.launcher.system_info['platform']}
Python: {self.launcher.system_info['python_version'].split()[0]}
Architecture: {self.launcher.system_info['architecture']}
Virtual Environment: {'✅ Available' if self.launcher.system_info['venv_exists'] else '❌ Not Found'}
Project Root: {self.launcher.system_info['project_root']}

Completed Phases: {len(self.launcher.project_status['phases_completed'])}
"""
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)
    
    def log_output(self, message: str):
        """Log output to the GUI."""
        self.output_text.insert(tk.END, f"{message}\n")
        self.output_text.see(tk.END)
        self.root.update()
    
    def show_status(self):
        """Show project status."""
        self.log_output("📊 Project Status:")
        for phase in self.launcher.project_status['phases_completed']:
            data_info = self.launcher.project_status['data_available'].get(phase, '')
            if isinstance(data_info, int):
                self.log_output(f"  ✅ {phase} ({data_info} items)")
            else:
                self.log_output(f"  ✅ {phase}")
    
    def install_deps(self):
        """Install dependencies."""
        self.log_output("🔧 Installing dependencies...")
        success = self.launcher.install_dependencies()
        if success:
            self.log_output("✅ Dependencies installed successfully!")
        else:
            self.log_output("❌ Failed to install dependencies!")
    
    def run_phase(self, phase: str):
        """Run a specific phase."""
        self.log_output(f"🚀 Running {phase}...")
        success = self.launcher.run_phase(phase)
        if success:
            self.log_output(f"✅ {phase} completed successfully!")
        else:
            self.log_output(f"❌ {phase} failed!")
        self.update_system_info()
    
    def run_all_phases(self):
        """Run all phases."""
        self.log_output("📈 Running all phases...")
        self.launcher.run_all_phases()
        self.update_system_info()
    
    def clean_data(self):
        """Clean project data."""
        self.log_output("🧹 Cleaning project data...")
        self.launcher.clean_project_data()
        self.log_output("✅ Project data cleaned!")
        self.update_system_info()
    
    def show_docs(self):
        """Show documentation."""
        self.log_output("📖 Available documentation:")
        docs = ['README.md', 'WIKIPEDIA_TUTORIAL.md', 'WIKIPEDIA_COLLECTION_SUMMARY.md']
        for doc in docs:
            doc_path = self.launcher.project_root / doc
            if doc_path.exists():
                self.log_output(f"  ✅ {doc}")
            else:
                self.log_output(f"  ❌ {doc} (not found)")
    
    def run(self):
        """Run the GUI."""
        self.root.mainloop()

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Food Recipes Setup & Launch System")
    parser.add_argument('--cli', action='store_true', help='Force CLI mode')
    parser.add_argument('--gui', action='store_true', help='Force GUI mode')
    parser.add_argument('--install-deps', action='store_true', help='Install dependencies only')
    parser.add_argument('--status', action='store_true', help='Show project status only')
    
    args = parser.parse_args()
    
    # Initialize launcher
    launcher = FoodRecipesLauncher()
    
    # Show banner
    launcher.print_banner()
    
    # Handle command line arguments
    if args.install_deps:
        launcher.install_dependencies()
        return
    
    if args.status:
        launcher.print_system_info()
        launcher.print_project_status()
        return
    
    # Choose interface
    if args.gui and GUI_AVAILABLE:
        gui = FoodRecipesGUI(launcher)
        gui.run()
    elif args.cli or not GUI_AVAILABLE:
        launcher.print_system_info()
        launcher.print_project_status()
        launcher.show_menu()
    else:
        # Ask user preference
        choice = input("Choose interface (g)ui or (c)li: ").lower().strip()
        if choice == 'g' and GUI_AVAILABLE:
            gui = FoodRecipesGUI(launcher)
            gui.run()
        else:
            launcher.print_system_info()
            launcher.print_project_status()
            launcher.show_menu()

if __name__ == "__main__":
    main()
