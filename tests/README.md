# Tests - MCP Hub Crawler

Infrastructure de tests automatisés.

## Structure

```
tests/
├── unit/          # Tests unitaires (modules individuels)
└── integration/   # Tests d'intégration (pipeline complet)
```

## 🚧 À Venir

Le projet ne possède pas encore de tests automatisés. Cette structure est préparée pour leur implémentation future.

### Tests Prioritaires à Implémenter

**Unit Tests** :
- `src/parsers/` - Parsers README, tools, parameters
- `src/enrichers/` - Enrichers GitHub, npm, etc.
- `src/scrapers/` - Base scraper

**Integration Tests** :
- Pipeline complet end-to-end
- Migration SQLite → Supabase
- Validation de l'intégrité des données

## Exécution (futur)

```bash
# Tests unitaires
pytest tests/unit/

# Tests d'intégration
pytest tests/integration/

# Tous les tests
pytest tests/

# Avec coverage
pytest --cov=src tests/
```

## Configuration

À créer :
- `pytest.ini` - Configuration pytest
- `conftest.py` - Fixtures partagées
- `.coveragerc` - Configuration coverage
