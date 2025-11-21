# Script d'Analyse de Base de Données MCP Servers

## 📋 Vue d'ensemble

Ce script TypeScript analyse la base de données SQLite des serveurs MCP et génère un rapport complet sur :

- **Configurations d'installation** : NPM, Docker, ou aucune config
- **Métriques GitHub** : Health scores, activité récente, popularité, qualité des projets
- **Complétude des données** : Proportions de présence pour chaque champ de chaque table
- **Insights clés** : Analyses automatiques et recommandations

## 🚀 Utilisation

### Option 1 : Double-cliquer sur le fichier .bat (Windows)

1. Double-cliquez sur `analyze-db.bat` à la racine du projet
2. Le script compile et exécute automatiquement l'analyse
3. Les résultats s'affichent dans la console
4. Un rapport Markdown est généré dans `reports/`

### Option 2 : Ligne de commande

```bash
# Depuis la racine du projet
npm run analyze

# Ou directement avec Node.js
node scripts/analyze-database.js

# Ou en mode développement avec TypeScript
npm run analyze:dev
```

## 📊 Rapport Généré

### Console (sortie colorée)

Le rapport console affiche :

```
🔍 ANALYSE BASE DE DONNÉES MCP SERVERS
Date: 2025-11-21

📊 STATISTIQUES GÉNÉRALES
┌─────────────────────┬───────────────────────┐
│ Total Serveurs      │ 199                   │
│ Avec GitHub Info    │ 198 (99.5%)           │
│ Avec Outils (Tools) │ 7 serveurs / 70 tools │
└─────────────────────┴───────────────────────┘

🔧 CONFIGURATIONS D'INSTALLATION
┌───────────────┬───────┬──────┐
│ Type Config   │ Count │ %    │
├───────────────┼───────┼──────┤
│ NPM Config    │ 0     │ 0%   │
│ Docker Config │ 0     │ 0%   │
│ Sans Config   │ 199   │ 100% │
└───────────────┴───────┴──────┘

⭐ FIABILITÉ GITHUB (Health Score)
...
```

### Fichier Markdown

Un rapport complet est généré dans :
```
reports/db-analysis-YYYY-MM-DD.md
```

Le rapport inclut :
- Tableaux formatés avec toutes les statistiques
- Distribution des stars par tranches
- Top 10 serveurs par popularité
- Langages primaires utilisés
- Complétude détaillée de tous les champs
- Insights et recommandations

## 📈 Statistiques Analysées

### 1. Configurations d'Installation
- Nombre de serveurs avec config NPM
- Nombre de serveurs avec config Docker
- Nombre de serveurs sans configuration
- Pourcentages respectifs

### 2. Fiabilité GitHub (Health Score 0-100)

Distribution par catégorie :
- **Excellent** (≥80%) : Projets très fiables
- **Bon** (≥60%) : Projets fiables
- **Moyen** (≥40%) : Projets moyennement fiables
- **Faible** (<40%) : Projets peu fiables
- **Inconnu** : Pas de données

### 3. Activité Récente

- **Commit frequency** : Moyenne et médiane (derniers 30 jours)
- **Derniers commits** :
  - < 1 mois : Projets très actifs
  - < 3 mois : Projets actifs
  - < 6 mois : Projets modérément actifs
  - \> 6 mois : Projets inactifs

### 4. Popularité

**Métriques moyennes et médianes** :
- GitHub Stars
- GitHub Forks
- GitHub Watchers
- Contributors

**Distribution des stars** :
- 0-100 stars
- 100-1000 stars
- 1000-10000 stars
- \>10000 stars

**Top 10** : Serveurs les plus populaires

### 5. Qualité des Projets

**Présence de fichiers standard** :
- README
- LICENSE
- CONTRIBUTING
- CODE_OF_CONDUCT

**Indicateurs de statut** :
- Archived (archivé)
- Disabled (désactivé)
- Fork (fork d'un autre projet)

**Langages primaires** : Distribution par langage

### 6. Complétude des Données

Pour chaque champ de chaque table :
```
github_info.github_stars: 198/199 (99.5%)
servers.tagline: 22/199 (11.06%)
npm_info.npm_package: 0/199 (0%)
```

Permet d'identifier :
- Les données bien remplies
- Les lacunes à combler
- Les champs inutilisés

### 7. Insights Clés

Analyses automatiques comme :
- "⚠️ 199 serveurs (100%) n'ont AUCUNE configuration d'installation"
- "✅ 11 serveurs (5.56%) ont un EXCELLENT score de santé (≥80%)"
- "🚀 19 serveurs sont ACTIFS (commit dans le dernier mois)"
- "⚖️ Seulement 19 serveurs (9.55%) ont une LICENSE"

## 🛠️ Structure des Fichiers

```
C:\GitHub\crawler MCPhub\
├── analyze-db.bat              # Exécutable Windows
├── package.json                # Dépendances npm
├── tsconfig.json               # Configuration TypeScript
├── scripts/
│   ├── analyze-database.ts     # Script principal (TypeScript)
│   ├── analyze-database.js     # Script compilé (JavaScript)
│   └── types/
│       └── database.types.ts   # Types TypeScript
├── data/
│   └── mcp_servers.db          # Base de données SQLite (7.3 MB)
└── reports/                    # Dossier des rapports générés
    └── db-analysis-YYYY-MM-DD.md
```

## 📦 Dépendances

- **better-sqlite3** : Accès rapide à SQLite
- **chalk** : Couleurs dans la console
- **cli-table3** : Tableaux formatés
- **date-fns** : Manipulation des dates
- **typescript** : Compilation TypeScript
- **ts-node** : Exécution TypeScript directe

## 🔧 Configuration

Aucune configuration requise ! Le script fonctionne out-of-the-box.

### Personnalisation (optionnelle)

Pour modifier les seuils de fiabilité, éditez `scripts/analyze-database.ts` :

```typescript
// Ligne ~178
if (score === null) {
  distribution.unknown++;
} else if (score >= 80) {  // ← Modifier ici (Excellent)
  distribution.excellent++;
} else if (score >= 60) {  // ← Modifier ici (Bon)
  distribution.good++;
} else if (score >= 40) {  // ← Modifier ici (Moyen)
  distribution.medium++;
} else {
  distribution.poor++;
}
```

Après modification, recompilez :
```bash
npx tsc scripts/analyze-database.ts --target ES2020 --module commonjs --lib ES2020 --esModuleInterop --skipLibCheck --resolveJsonModule --moduleResolution node
```

## 📊 Exemple de Sortie

### Console

![Console Output](https://via.placeholder.com/800x600.png?text=Console+Output)

### Markdown

Voir `reports/db-analysis-2025-11-21.md` pour un exemple complet.

## ⚡ Performance

- **Temps d'exécution** : ~1-2 secondes
- **Taille DB** : 7.3 MB (199 serveurs)
- **Mémoire** : ~50 MB

## 🐛 Dépannage

### Erreur "Cannot find module"

```bash
# Réinstaller les dépendances
npm install
```

### Erreur "Database not found"

Vérifiez que `data/mcp_servers.db` existe :
```bash
dir data\mcp_servers.db
```

### Erreur de compilation TypeScript

```bash
# Compiler manuellement
npx tsc scripts/analyze-database.ts --target ES2020 --module commonjs --lib ES2020 --esModuleInterop --skipLibCheck --resolveJsonModule --moduleResolution node
```

## 📝 Notes

- Le script est en **lecture seule** (readonly) : il ne modifie JAMAIS la base de données
- Les rapports Markdown sont horodatés pour éviter les écrasements
- Les couleurs console fonctionnent dans tous les terminaux modernes (Windows Terminal, cmd.exe, PowerShell, Git Bash)

## 🚀 Améliorations Futures

- Export JSON des statistiques
- Export CSV pour Excel
- Graphiques ASCII dans la console
- Comparaison entre deux analyses (diff)
- Alertes configurables (email, webhook)
- Mode watch (analyse automatique périodique)

---

**Créé par :** Script TypeScript d'analyse de base de données
**Version :** 1.0.0
**Date :** 2025-11-21
