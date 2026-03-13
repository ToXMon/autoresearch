#!/usr/bin/env python3
"""
Visualize autoresearch experiment results
Generates charts and summary for sharing
"""

import os
from pathlib import Path
from datetime import datetime

# Try to import matplotlib, if not available create text-based visualization
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

def generate_text_dashboard(results):
    """Generate text-based dashboard for terminal sharing"""
    
    # Header
    print("\033[95m" + "="*70 + "\033[0m")
    print("\033[95m         🚀 AutoResearch on Akash - Experiment Dashboard\033[0m")
    print("\033[95m" + "="*70 + "\033[0m")
    print()
    
    # Progress chart (ASCII)
    print("\033[96m📈 Val BPB Progress Over Experiments:\033[0m")
    print()
    
    min_bpb = min(r['val_bpb'] for r in results)
    max_bpb = max(r['val_bpb'] for r in results)
    
    for i, result in enumerate(results, 1):
        status_emoji = "✅" if result['status'] == 'keep' else "❌"
        bpb_normalized = int((result['val_bpb'] - min_bpb) / (max_bpb - min_bpb + 0.001) * 30)
        bar = "█" * bpb_normalized + "░" * (30 - bpb_normalized)
        
        color = "\033[92m" if result['status'] == 'keep' else "\033[91m"
        print(f"{color}Exp {i:2d} {status_emoji} |{bar}| {result['val_bpb']:.6f}\033[0m")
    
    print()
    
    # Summary stats
    successes = sum(1 for r in results if r['status'] == 'keep')
    total = len(results)
    
    print("\033[93m📊 Summary Statistics:\033[0m")
    print(f"   ✅ Successful experiments: {successes}/{total} ({successes/total*100:.1f}%)")
    print(f"   📉 Best val_bpb: {min_bpb:.6f}")
    print(f"   📈 Worst val_bpb: {max_bpb:.6f}")
    
    baseline = results[0]['val_bpb'] if results else 0
    improvement = ((baseline - min_bpb) / baseline * 100) if baseline > 0 else 0
    print(f"   🎯 Total improvement: {improvement:.1f}%")
    
    print()
    print("\033[95m" + "="*70 + "\033[0m")
    print("\033[92m🚀 Share on X: cat SOCIAL_POST.md\033[0m")
    print("\033[92m📖 Full results: cat results.tsv\033[0m")
    print("\033[95m" + "="*70 + "\033[0m")
    print()

def generate_matplotlib_dashboard(results):
    """Generate matplotlib charts"""
    if not HAS_MATPLOTLIB:
        return
        
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('AutoResearch on Akash - Experiment Results', fontsize=16, fontweight='bold')
    
    # 1. Line chart of val_bpb over experiments
    ax1 = axes[0, 0]
    experiments = [r['experiment'] for r in results]
    val_bpbs = [r['val_bpb'] for r in results]
    colors = ['green' if r['status'] == 'keep' else 'red' for r in results]
    
    ax1.plot(experiments, val_bpbs, 'b-', alpha=0.3, linewidth=2)
    ax1.scatter(experiments, val_bpbs, c=colors, s=100, zorder=5)
    ax1.set_xlabel('Experiment #')
    ax1.set_ylabel('Val BPB')
    ax1.set_title('Validation BPB Over Time')
    ax1.grid(True, alpha=0.3)
    
    # 2. Success/failure pie chart
    ax2 = axes[0, 1]
    successes = sum(1 for r in results if r['status'] == 'keep')
    failures = len(results) - successes
    ax2.pie([successes, failures], labels=['Success', 'Failed'], 
            colors=['#90EE90', '#FFB6C1'], autopct='%1.1f%%', startangle=90)
    ax2.set_title('Experiment Success Rate')
    
    # 3. Improvement over baseline
    ax3 = axes[1, 0]
    baseline = results[0]['val_bpb'] if results else 0
    improvements = [(baseline - r['val_bpb']) / baseline * 100 for r in results]
    ax3.bar(experiments, improvements, color=colors, alpha=0.7)
    ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax3.set_xlabel('Experiment #')
    ax3.set_ylabel('Improvement vs Baseline (%)')
    ax3.set_title('Performance Improvement')
    ax3.grid(True, alpha=0.3)
    
    # 4. Summary stats text
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    min_bpb = min(val_bpbs)
    total_improvement = ((baseline - min_bpb) / baseline * 100) if baseline > 0 else 0
    
    summary_text = f"""
    EXPERIMENT SUMMARY
    ─────────────────────
    Total Experiments: {len(results)}
    Successful: {successes} ({successes/len(results)*100:.1f}%)
    Failed: {failures}
    
    PERFORMANCE
    ─────────────────────
    Baseline BPB: {baseline:.6f}
    Best BPB: {min_bpb:.6f}
    Improvement: {total_improvement:.1f}%
    
    COST ANALYSIS
    ─────────────────────
    Est. Akash Cost: ~{len(results) * 0.1:.1f} AKT (${len(results) * 0.02:.2f})
    Est. LLM Cost: ~${len(results) * 0.75:.2f}
    Total: ~${len(results) * 0.77:.2f}
    
    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    ax4.text(0.1, 0.5, summary_text, transform=ax4.transAxes, 
             fontsize=12, verticalalignment='center', fontfamily='monospace')
    
    plt.tight_layout()
    plt.savefig('experiment_dashboard.png', dpi=150, bbox_inches='tight')
    print("✅ Saved dashboard to experiment_dashboard.png")

def load_results_from_tsv(filepath="results.tsv"):
    """Load results from TSV file"""
    results = []
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[1:], 1):  # Skip header
                if line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) >= 4:
                        results.append({
                            'experiment': i,
                            'commit': parts[0],
                            'val_bpb': float(parts[1]),
                            'memory_gb': float(parts[2]),
                            'status': parts[3],
                            'description': parts[4] if len(parts) > 4 else ''
                        })
    except FileNotFoundError:
        # Generate demo results
        print("⚠️  No results.tsv found, generating demo data...")
        import random
        baseline_bpb = 2.0
        for i in range(1, 26):
            # Simulate realistic improvement curve
            improvement = random.uniform(0.001, 0.05) if random.random() > 0.3 else 0
            baseline_bpb = max(1.5, baseline_bpb - improvement if random.random() > 0.4 else baseline_bpb + random.uniform(0.01, 0.05))
            
            results.append({
                'experiment': i,
                'commit': f'demo_{i:04d}',
                'val_bpb': baseline_bpb + random.uniform(-0.02, 0.02),
                'memory_gb': random.uniform(8.5, 12.5),
                'status': 'keep' if random.random() > 0.35 else 'discard',
                'description': f'Demo experiment {i}'
            })
    
    return results

if __name__ == "__main__":
    results = load_results_from_tsv()
    
    # Always show text dashboard
    generate_text_dashboard(results)
    
    # Generate matplotlib if available
    if HAS_MATPLOTLIB:
        generate_matplotlib_dashboard(results)
    else:
        print("\n💡 Install matplotlib for image export: pip install matplotlib")
