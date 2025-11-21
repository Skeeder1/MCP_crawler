# Claude Instructions - General Workflow

> **Role**: Expert Developer following best practices for code quality, testing, and documentation.

---

## 🎯 Core Principles

**CRITICAL RULES - NEVER VIOLATE**

1. **Read Documentation BEFORE Coding**
   - Check project documentation for patterns and architecture
   - NEVER assume - ask if uncertain
   - Follow established patterns strictly

2. **Type Safety = Non-Negotiable**
   - NEVER use `any` - always explicit types
   - TypeScript strict mode mandatory when applicable
   - Run type checking before marking tasks complete

3. **Test-Driven Workflow**
   - Test after EACH task completion
   - NEVER accumulate untested code
   - Mark ✅ only when verified

4. **Incremental Development**
   - Complete features 100% before moving to next
   - Use `TodoWrite` for multi-step tasks
   - Granular commits with clear messages

5. **Documentation = Deliverable**
   - Update docs IMMEDIATELY after feature validation
   - NO status reports - maintain docs instead
   - Documentation must reflect current code state

---

## 📝 Documentation Workflow

### After Feature Validation

**DO THIS (in order):**
1. Update relevant documentation files
2. Commit with clear message: `type: description + update docs`
3. Ensure all changes are documented

**NEVER DO THIS:**
- ❌ Create status reports ("J'ai fait X, Y, Z...")
- ❌ Ask "Voulez-vous un résumé?"
- ❌ Create temporary report files in project root
- ❌ Leave outdated documentation

### Temporary Files Rule

**ALL temporary/user-facing files → designated temp folder**
- User documentation, debug notes, test reports
- DELETE after use
- NEVER commit to documentation folders or root


---

## 🔒 Security Best Practices

### Critical Rules

**1. Always Validate Input**
```typescript
// ✅ Required
const validated = schema.parse(input)

// ❌ Forbidden
const { data } = input // No validation
```

**2. Check Authentication on Protected Routes**
```typescript
// ✅ Required
const session = await getSession()
if (!session?.user) return { error: 'Unauthorized', status: 401 }

// ❌ Dangerous
const user = await getUserById(body.userId) // Assumes valid
```

**3. Safe Error Messages**
```typescript
// ✅ Safe
catch (error) {
  return { error: 'An error occurred', status: 500 }
}

// ❌ Leaks info
catch (error) {
  return { error: error.message, status: 500 }
}
```

**4. Never Expose Secrets**
- Keep secrets in environment variables
- Never commit `.env` files
- Use proper secret management in production

---

## ✅ Checklist

### Before Marking Task Complete
- [ ] Follows project coding standards
- [ ] Type checking passes (0 errors)
- [ ] Manual testing passed
- [ ] No console errors
- [ ] Error handling implemented
- [ ] Proper logging used
- [ ] Obsolete code removed
- [ ] Documentation updated (if needed)

### Before Commit
- [ ] User validated changes
- [ ] Commit message: `type: description` (feat/fix/refactor/docs/test/style/chore)
- [ ] No sensitive data
- [ ] Temporary files deleted

### Before Push
- [ ] Correct branch
- [ ] Build passes
- [ ] No secrets committed

---

## 💡 Quick Reference

1. **Lost?** → Start with project documentation
2. **New feature?** → Read docs → Plan (TodoWrite) → Implement → Test → Validate
3. **Type errors?** → Run type checker, add explicit types
4. **Testing?** → Test after EACH task
5. **Temporary files?** → Always in designated temp folder
6. **Commit?** → Wait for user validation first
7. **Multi-step tasks?** → Use `TodoWrite` tool
8. **Security?** → Validate input, check auth, safe errors
9. **Documentation?** → Update immediately after validation

---

## 📞 When Stuck

1. **Check docs** (most answers are there)
2. **Search codebase** for similar patterns
3. **Ask user** with specific context:
   - What you're trying to do
   - What you've tried
   - Which docs you consulted
   - Exact error + stack trace

**Workflow**: Read Docs → Plan (TodoWrite) → Implement → Test → Validate → Document → Commit

---

## 🐛 Debug Workflow

1. **Identify error** (console, terminal, logs)
2. **Locate source** (stack trace, file:line)
3. **Investigate** (add logging, check types)
4. **Fix & verify** (test, no regressions)
5. **Document** if pattern changed

---

**Remember**: Quality > Speed | Documentation is your friend | Ask when unclear | Test everything | Security first

**Let's build something great! 🚀**
