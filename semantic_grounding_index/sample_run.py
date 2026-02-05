"""Sample run demonstrating SGI computation with positive and negative examples."""

import sys
from core import sgi
from openai_embedder import get_embedder


def run_example(example_name: str, question: str, context: str, response: str, embedder, provider_name: str):
    """Run a single SGI example and display results."""
    print("\n" + "=" * 80)
    print(f"Example: {example_name}")
    print("=" * 80)
    print("\nQuestion:")
    print("-" * 80)
    print(question)
    print("\nContext (retrieved evidence):")
    print("-" * 80)
    print(context[:200] + "..." if len(context) > 200 else context)
    print("\nResponse:")
    print("-" * 80)
    print(response[:200] + "..." if len(response) > 200 else response)
    print("\n" + "=" * 80)
    
    print("\nComputing SGI metric...")
    
    # Compute SGI
    result = sgi(q=question, c=context, r=response, embedder=embedder)
    
    # Display results
    print("\n" + "=" * 80)
    print("Results:")
    print("=" * 80)
    print(f"SGI:              {result['sgi']:.6f}")
    print(f"θ(r,q):           {result['theta_rq']:.6f} radians")
    print(f"θ(r,c):           {result['theta_rc']:.6f} radians")
    print("=" * 80)
    
    # Interpretation
    print("\nInterpretation:")
    if result['sgi'] > 1.0:
        print(f"✓ High SGI ({result['sgi']:.2f}) - Response is well-grounded in context.")
        print("  The response is semantically closer to the context than to the question.")
    else:
        print(f"⚠ Low SGI ({result['sgi']:.2f}) - Response is more aligned with question than context.")
        print("  The response may not be well-grounded in the provided context.")
    
    print(f"\nAngular distance from response to question: {result['theta_rq']:.4f} radians")
    print(f"Angular distance from response to context:   {result['theta_rc']:.4f} radians")
    
    return result


def main():
    """Run SGI computation on positive and negative examples."""
    
    # Determine provider from command line or auto-detect
    provider = None
    if len(sys.argv) > 1:
        provider = sys.argv[1].lower()
        if provider not in ["azure", "openai"]:
            print(f"Unknown provider: {provider}. Use 'azure' or 'openai'", file=sys.stderr)
            return 1
    
    print("=" * 80)
    print("SGI (Semantic Grounding Index) Sample Run")
    print("=" * 80)
    provider_name = provider or "auto-detected"
    print(f"\nUsing {provider_name} provider for embeddings")
    
    # Example 1: Positive example - well-grounded response
    question_positive = (
        "What is machine learning and how does supervised learning differ from unsupervised learning?"
    )
    
    context_positive = (
        "Machine learning is a subset of artificial intelligence that enables systems to learn "
        "and improve from experience without being explicitly programmed. It focuses on the development "
        "of computer programs that can access data and use it to learn for themselves. The process of "
        "learning begins with observations or data, such as examples, direct experience, or instruction, "
        "in order to look for patterns in data and make better decisions in the future based on the "
        "examples that we provide.\n\n"
        "Supervised learning is a type of machine learning where algorithms learn from labeled training data. "
        "The algorithm is provided with input-output pairs, where the input is the data and the output is "
        "the correct label or value. The goal is to learn a mapping function from inputs to outputs so that "
        "when new, unseen data is provided, the algorithm can predict the correct output. Common examples "
        "include classification tasks (like spam detection) and regression tasks (like predicting house prices).\n\n"
        "Unsupervised learning, on the other hand, involves algorithms that learn patterns from data without "
        "labeled examples. The system is given only input data without corresponding output labels. The algorithm "
        "must find hidden patterns, structures, or relationships in the data on its own. Common techniques include "
        "clustering (grouping similar data points together) and dimensionality reduction (reducing the number of "
        "features while preserving important information).\n\n"
        "The key difference is that supervised learning uses labeled data to learn a function that maps inputs to "
        "outputs, while unsupervised learning discovers hidden patterns in unlabeled data without guidance."
    )
    
    response_positive = (
        "Machine learning is a branch of artificial intelligence that allows computer systems to automatically "
        "learn and improve from experience without being explicitly programmed. It works by analyzing data to "
        "identify patterns and make predictions or decisions.\n\n"
        "Supervised learning is a machine learning approach where the algorithm learns from labeled training examples. "
        "The model is trained on input-output pairs, where each input has a corresponding correct output label. "
        "The algorithm learns to map inputs to outputs, enabling it to make predictions on new, unseen data. "
        "Examples include email spam classification and predicting numerical values like house prices.\n\n"
        "Unsupervised learning differs in that it works with unlabeled data. The algorithm receives only input data "
        "without any corresponding output labels and must discover patterns, structures, or relationships on its own. "
        "Common applications include clustering similar data points together and reducing the complexity of data while "
        "maintaining important information.\n\n"
        "The fundamental distinction is that supervised learning uses labeled examples to learn input-to-output "
        "mappings, whereas unsupervised learning finds hidden patterns in data without any labeled guidance."
    )
    
    # Example 2: Negative example - context is unrelated to the question
    question_negative = (
        "What is machine learning and how does supervised learning differ from unsupervised learning?"
    )
    
    # Context is about cooking, completely unrelated to machine learning
    context_negative = (
        "French cuisine is renowned worldwide for its sophisticated techniques and emphasis on fresh, high-quality "
        "ingredients. The foundation of French cooking lies in mastering basic techniques such as sautéing, braising, "
        "and making stocks. Classic French dishes often begin with a mirepoix - a combination of diced carrots, celery, "
        "and onions that forms the flavor base for many soups and stews.\n\n"
        "One of the most important techniques in French cooking is the creation of sauces. The five mother sauces "
        "form the foundation: béchamel (white sauce), velouté (velvet sauce), espagnole (brown sauce), hollandaise "
        "(emulsified butter sauce), and tomato sauce. From these, countless derivative sauces can be created.\n\n"
        "Pastry work is another cornerstone of French cuisine, with techniques like making pâte brisée (shortcrust pastry) "
        "and pâte feuilletée (puff pastry) requiring precision and practice. French desserts like crème brûlée, "
        "tarte tatin, and éclairs showcase the artistry of French pastry chefs.\n\n"
        "Regional variations add diversity to French cuisine. Provence is known for Mediterranean influences with herbs "
        "like rosemary and thyme, while Normandy features rich cream and butter-based dishes. Alsace incorporates German "
        "influences, and the southwest uses duck fat and hearty ingredients."
    )
    
    # Response still answers the machine learning question (not using the cooking context)
    response_negative = (
        "Machine learning is a branch of artificial intelligence that allows computer systems to automatically "
        "learn and improve from experience without being explicitly programmed. It works by analyzing data to "
        "identify patterns and make predictions or decisions.\n\n"
        "Supervised learning is a machine learning approach where the algorithm learns from labeled training examples. "
        "The model is trained on input-output pairs, where each input has a corresponding correct output label. "
        "The algorithm learns to map inputs to outputs, enabling it to make predictions on new, unseen data. "
        "Examples include email spam classification and predicting numerical values like house prices.\n\n"
        "Unsupervised learning differs in that it works with unlabeled data. The algorithm receives only input data "
        "without any corresponding output labels and must discover patterns, structures, or relationships on its own. "
        "Common applications include clustering similar data points together and reducing the complexity of data while "
        "maintaining important information.\n\n"
        "The fundamental distinction is that supervised learning uses labeled examples to learn input-to-output "
        "mappings, whereas unsupervised learning finds hidden patterns in data without any labeled guidance."
    )
    
    try:
        # Initialize embedder (auto-detects if provider not specified)
        embedder = get_embedder(provider=provider)
        
        # Run positive example
        result_positive = run_example(
            "Positive Example (Well-Grounded)",
            question_positive,
            context_positive,
            response_positive,
            embedder,
            provider_name
        )
        
        # Run negative example
        result_negative = run_example(
            "Negative Example (Poorly Grounded)",
            question_negative,
            context_negative,
            response_negative,
            embedder,
            provider_name
        )
        
        # Summary comparison
        print("\n" + "=" * 80)
        print("Summary Comparison")
        print("=" * 80)
        print(f"\nPositive Example SGI: {result_positive['sgi']:.4f}")
        print(f"Negative Example SGI: {result_negative['sgi']:.4f}")
        print(f"\nDifference: {result_positive['sgi'] - result_negative['sgi']:.4f}")
        print("\nThe positive example shows a well-grounded response (high SGI),")
        print("while the negative example demonstrates poor grounding (low SGI)")
        print("when the context is unrelated to the question.")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure you have set the appropriate environment variables:")
        print("  For Azure OpenAI:")
        print("    - AZURE_OPENAI_API_KEY")
        print("    - AZURE_OPENAI_ENDPOINT")
        print("  For OpenAI:")
        print("    - OPENAI_API_KEY")
        print("\nOr specify provider: python sample_run.py azure  or  python sample_run.py openai")
        return 1


if __name__ == "__main__":
    exit(main())
