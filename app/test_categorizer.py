2"""
Script de prueba del categorizador sin necesidad de Telegram.
Permite probar la lógica de categorización por consola.
"""

from app.bot.categorizer import MessageCategorizer
from app.models import Category
from app.utils import FormatterHelper


class CategorizerTester:
    """Clase para probar el categorizador con datos de prueba."""
    
    def __init__(self):
        self.categorizer = MessageCategorizer()
        self.test_categories = self._create_test_categories()
    
    def _create_test_categories(self) -> list[Category]:
        return [
            Category(
                id=1,
                name="trabajo",
                keywords=["reunion", "meeting", "oficina", "proyecto", "deadline", "tarea"]
            ),
            Category(
                id=2,
                name="personal",
                keywords=["familia", "casa", "hogar", "amigos", "cumpleaños"]
            ),
            Category(
                id=3,
                name="compras",
                keywords=["tienda", "mercado", "comprar", "shopping", "precio"]
            ),
            Category(
                id=4,
                name="urgente",
                keywords=["importante", "critico", "emergencia", "ya", "ahora"]
            ),
            Category(
                id=5,
                name="finanzas",
                keywords=["pago", "factura", "banco", "dinero", "transferencia"]
            )
        ]
    
    def test_messages(self):
        test_cases = [
            "Tengo una reunion importante mañana en la oficina",
            "Voy a casa con mi familia",
            "Necesito comprar pan en la tienda",
            "Es urgente que veamos esto ahora",
            "Tengo que hacer el pago de la factura del banco",
            "Proyecto deadline para el viernes",
            "Celebrar cumpleaños de mi amigo",
            "Este es un mensaje sin categoria clara",
            "Meeting con el equipo",
            "Transferencia bancaria pendiente"
        ]
        
        print("=" * 70)
        print("PRUEBA DEL CATEGORIZADOR DE MENSAJES")
        print("=" * 70)
        print()
        
        for idx, message in enumerate(test_cases, 1):
            result = self.categorizer.categorize_message(message, self.test_categories)
            
            confidence_formatted = FormatterHelper.format_confidence_score(
                result['confidence_score']
            )
            
            print(f"Prueba #{idx}")
            print(f"Mensaje: {message}")
            print(f"Categoría: {result['category']}")
            print(f"Confianza: {confidence_formatted}")
            print("-" * 70)
    
    def test_detailed_scores(self, message: str):
        print("\n" + "=" * 70)
        print("ANÁLISIS DETALLADO DE SCORES")
        print("=" * 70)
        print(f"\nMensaje: {message}\n")
        
        scores = self.categorizer.get_category_scores(message, self.test_categories)
        
        print(f"{'Categoría':<15} {'Score':<10} {'Exact':<10} {'Fuzzy':<10}")
        print("-" * 70)
        
        for score_data in scores:
            print(
                f"{score_data['category']:<15} "
                f"{score_data['score']:.3f}     "
                f"{score_data['exact_matches']:.3f}     "
                f"{score_data['fuzzy_similarity']:.3f}"
            )
        
        print("\n" + "=" * 70)
    
    def interactive_test(self):
        print("\n" + "=" * 70)
        print("MODO INTERACTIVO - Prueba tus propios mensajes")
        print("=" * 70)
        print("\nCategorías disponibles:")
        for cat in self.test_categories:
            keywords_str = ", ".join(cat.keywords[:5])
            print(f"  • {cat.name}: {keywords_str}...")
        
        print("\nEscribe 'salir' para terminar\n")
        
        while True:
            user_input = input("Mensaje a categorizar: ").strip()
            
            if user_input.lower() in ['salir', 'exit', 'quit']:
                print("¡Hasta luego!")
                break
            
            if not user_input:
                continue
            
            result = self.categorizer.categorize_message(user_input, self.test_categories)
            confidence_formatted = FormatterHelper.format_confidence_score(
                result['confidence_score']
            )
            
            print(f"→ Categoría: {result['category']}")
            print(f"→ Confianza: {confidence_formatted}\n")


def main():
    tester = CategorizerTester()
    
    tester.test_messages()
    
    tester.test_detailed_scores("Tengo una reunion urgente en la oficina")
    
    tester.interactive_test()


if __name__ == "__main__":
    main()