# 🔄 Migration Guide v3.2

<div align="center">

![Migration Guide](https://img.shields.io/badge/guide-migration-orange)
![Version](https://img.shields.io/badge/version-v3.2-blue)
![Status](https://img.shields.io/badge/status-complete-success)

**🚀 Complete migration guide for RadioX Backend separation**

[🏠 Documentation](../) • [👨‍💻 Developer Guides](../README.md#-developer-guides) • [🔧 Development](development.md)

</div>

---

## 🎯 Overview

RadioX v3.2 introduces a **major architectural change**: Das Backend wurde von der Frontend-Monorepo getrennt und ist jetzt ein eigenständiges Repository.

### ✨ **Migration Highlights**
- 🏗️ **Repository Separation** - Backend ist jetzt eigenständig
- 📁 **Path Corrections** - Alle internen Pfade wurden korrigiert
- 🔧 **Dependency Management** - Vollständige requirements.txt
- ⚙️ **Configuration** - .env liegt jetzt im Root

---

## 🔄 What Changed

### **📁 Directory Structure Migration**

| **Before (v3.1)** | **After (v3.2)** | **Status** |
|-------------------|-------------------|------------|
| `RadioX/backend/` | `radiox-backend/` | ✅ Migrated |
| `RadioX/.env` | `radiox-backend/.env` | ✅ Moved |
| `RadioX/backend/src/` | `radiox-backend/src/` | ✅ Updated |

### **🔧 Path Corrections Applied**

| **File** | **Old Path** | **New Path** | **Reason** |
|----------|--------------|--------------|------------|
| `config/settings.py` | `parent.parent.parent` | `parent.parent` | Root directory changed |
| Audio Generation Service | `parent.parent` | `parent.parent.parent` | Incorrect relative path |
| Image Generation Service | `parent.parent` | `parent.parent.parent` | Incorrect relative path |
| Broadcast Generation Service | `parent.parent` | `parent.parent.parent` | Incorrect relative path |
| Supabase Service | `parent.parent` | `parent.parent.parent` | Incorrect relative path |

### **📦 Dependencies Updated**

| **Package** | **Status** | **Purpose** |
|-------------|------------|-------------|
| `pydantic-settings` | ✅ Added | Settings management |
| `supabase` | ✅ Added | Database client |
| `Pillow` | ✅ Added | Image processing |

---

## 🚀 Migration Steps

### **🔄 For Existing Developers**

```bash
# 1. Backup your current work
cd RadioX/backend
git stash  # Save any uncommitted changes

# 2. Clone the new repository
cd ..
git clone https://github.com/your-org/radiox-backend.git

# 3. Copy your .env file
cp .env radiox-backend/.env

# 4. Setup new environment
cd radiox-backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# 5. Test the migration
python main.py --test
```

### **🆕 For New Developers**

```bash
# 1. Clone the backend repository
git clone https://github.com/your-org/radiox-backend.git
cd radiox-backend

# 2. Setup environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure API keys
cp env_template.txt .env
nano .env  # Add your API keys

# 4. Test system
python main.py --test
```

---

## 🔧 Technical Details

### **📂 Path Resolution Logic**

#### **Before (v3.1):**
```python
# config/settings.py
ROOT_DIR = Path(__file__).parent.parent.parent  # 3 levels up
# From: RadioX/backend/config/settings.py
# To:   RadioX/ (to find .env)
```

#### **After (v3.2):**
```python
# config/settings.py  
ROOT_DIR = Path(__file__).parent.parent  # 2 levels up
# From: radiox-backend/config/settings.py
# To:   radiox-backend/ (to find .env)
```

### **🔗 Service Import Paths**

#### **Generation Services Fixed:**
```python
# Before (WRONG):
sys.path.append(str(Path(__file__).parent.parent))
# From: src/services/generation/audio_generation_service.py
# Would point to: src/services/ (missing config/)

# After (CORRECT):
sys.path.append(str(Path(__file__).parent.parent.parent))
# From: src/services/generation/audio_generation_service.py  
# Points to: radiox-backend/ (can find config/)
```

### **🗄️ Database Paths Verified:**
```python
# These were already correct:
sys.path.append(str(Path(__file__).parent.parent.parent))
# From: src/services/data/rss_service.py
# Points to: radiox-backend/ (can find database/)
```

---

## ✅ Verification

### **🧪 Test All Paths Work:**

```bash
# Test configuration loading
python -c "from config.settings import get_settings; print('✅ Settings loaded')"

# Test service imports
python -c "import main; print('✅ Main module loaded')"

# Test CLI tools
python main.py --help

# Test data collection
python cli/cli_data_collection.py --test
```

### **📊 Expected Output:**
```
✅ Settings loaded
✅ Main module loaded
✅ CLI help displayed
✅ Data collection test passed
```

---

## 🚨 Common Issues

### **❌ Import Errors**

**Problem:** `ModuleNotFoundError: No module named 'config'`

**Solution:**
```bash
# Check you're in the right directory
pwd  # Should show: .../radiox-backend

# Check Python path
python -c "import sys; print(sys.path)"

# Reinstall dependencies
pip install -r requirements.txt
```

### **❌ Missing Dependencies**

**Problem:** `ModuleNotFoundError: No module named 'pydantic_settings'`

**Solution:**
```bash
pip install pydantic-settings supabase Pillow
```

### **❌ Environment Issues**

**Problem:** `.env` file not found

**Solution:**
```bash
# Check .env exists in root
ls -la .env

# Copy from template if missing
cp env_template.txt .env
```

---

## 📈 Benefits

### **🎯 Improved Architecture:**
- ✅ **Cleaner Separation** - Backend is now independent
- ✅ **Simplified Paths** - No more complex relative imports
- ✅ **Better Dependencies** - Complete requirements.txt
- ✅ **Easier Development** - Direct backend development

### **🚀 Development Benefits:**
- ✅ **Faster Setup** - Single repository clone
- ✅ **Clearer Structure** - No frontend confusion
- ✅ **Better Testing** - Isolated backend testing
- ✅ **Easier Deployment** - Independent backend deployment

---

## 🤝 Support

### **📞 Need Help?**

| Issue Type | Contact |
|------------|---------|
| **Migration Problems** | [Create Issue](https://github.com/your-org/radiox-backend/issues) |
| **Path Errors** | Check this guide first |
| **Dependency Issues** | Run `pip install -r requirements.txt` |
| **General Questions** | [Developer Guide](development.md) |

---

<div align="center">

**Migration completed successfully! 🎉**

[🔧 Development Guide](development.md) • [🏗️ Architecture](architecture.md) • [🧪 Testing](testing.md)

</div> 