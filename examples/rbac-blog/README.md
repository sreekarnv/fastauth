# RBAC Blog Example

This example demonstrates how to implement **Role-Based Access Control (RBAC)** in a blog application using FastAuth.

## 🎯 What This Example Demonstrates

- ✅ **Three Roles**: Admin, Editor, Viewer with different permission levels
- ✅ **Four Permissions**: create_post, edit_post, publish_post, delete_post
- ✅ **Protected Routes**: Using `require_role()` and `require_permission()` dependencies
- ✅ **Permission-Based Access**: Fine-grained control over who can do what
- ✅ **Blog Post Management**: Create, edit, publish, and delete posts
- ✅ **Seed Script**: Automatically set up roles, permissions, and test users

## 📋 Prerequisites

- Python 3.11+
- Basic understanding of FastAPI and RBAC concepts

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
# Navigate to this example directory
cd examples/rbac-blog

# Install FastAuth (FastAPI is a peer dependency)
pip install sreekarnv-fastauth

# Install FastAPI and uvicorn
pip install fastapi uvicorn[standard]

# OR install from parent directory (for development)
pip install -e ../..
pip install fastapi uvicorn[standard]

# OR install all dependencies from requirements.txt
pip install -r requirements.txt
```

> **Note:** FastAPI is a peer dependency and must be installed separately.

### Step 2: Set Up Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# (Optional) Edit .env and customize settings
```

Your `.env` should look like:
```bash
JWT_SECRET_KEY=your-strong-secret-key-here
DATABASE_URL=sqlite:///./rbac_blog.db
REQUIRE_EMAIL_VERIFICATION=false
```

**🔐 Security Note:** Use a strong secret key in production! Generate one with:
```bash
openssl rand -hex 32
```

### Step 3: Seed the Database

The seed script creates roles, permissions, and test users:

```bash
# Run the seed script
python -m app.seed
```

This will create:
- **3 Roles**: viewer, editor, admin
- **4 Permissions**: create_post, edit_post, publish_post, delete_post
- **3 Test Users** (see below)

### Step 4: Run the Application

```bash
# Run the FastAPI app
uvicorn app.main:app --reload
```

The application will start at: **http://localhost:8000**

### Step 5: Test RBAC Features

1. **Open your browser:** http://localhost:8000
2. **Use the interactive API docs:** http://localhost:8000/docs
3. **Login with test accounts** (see below)
4. **Test different permissions** with different roles

## 👥 Roles & Permissions

### Role Hierarchy

```
┌─────────────────────────────────────────────┐
│                   Admin                     │
│  ⚡ Full control over blog and users        │
│  Permissions:                               │
│  • create_post                              │
│  • edit_post                                │
│  • publish_post                             │
│  • delete_post                              │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│                  Editor                     │
│  ✍️ Create and edit blog posts              │
│  Permissions:                               │
│  • create_post                              │
│  • edit_post                                │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│                  Viewer                     │
│  👤 Read-only access to published content   │
│  Permissions:                               │
│  • None (can only view published posts)     │
└─────────────────────────────────────────────┘
```

### Permission Matrix

| Action | Viewer | Editor | Admin |
|--------|--------|--------|-------|
| View published posts | ✅ | ✅ | ✅ |
| View draft posts | ❌ | ✅ | ✅ |
| Create posts | ❌ | ✅ | ✅ |
| Edit posts | ❌ | ✅ | ✅ |
| Publish/unpublish posts | ❌ | ❌ | ✅ |
| Delete posts | ❌ | ❌ | ✅ |
| View all users | ❌ | ❌ | ✅ |

## 🧪 Test Accounts

The seed script creates these test accounts:

| Role | Email | Password | Can Do |
|------|-------|----------|---------|
| **Viewer** | viewer@example.com | password123 | View published posts only |
| **Editor** | editor@example.com | password123 | Create and edit posts |
| **Admin** | admin@example.com | password123 | Everything (full access) |

## 🔌 API Endpoints

### Authentication

```bash
# Register a new user (auto-assigned viewer role)
POST /register
{
  "email": "user@example.com",
  "password": "password123"
}

# Login and get access token
POST /login
{
  "email": "admin@example.com",
  "password": "password123"
}

# Get current user info with roles and permissions
GET /me
Authorization: Bearer <access_token>
```

### Blog Posts

```bash
# List posts (published for all, all posts for editors+)
GET /posts?published_only=true
Authorization: Bearer <access_token>

# Create a new post (requires: create_post permission)
POST /posts
Authorization: Bearer <access_token>
{
  "title": "My First Post",
  "content": "This is my first blog post!"
}

# Get a single post
GET /posts/{post_id}
Authorization: Bearer <access_token>

# Update a post (requires: edit_post permission)
PATCH /posts/{post_id}
Authorization: Bearer <access_token>
{
  "title": "Updated Title",
  "content": "Updated content"
}

# Publish or unpublish a post (requires: publish_post permission)
POST /posts/{post_id}/publish
Authorization: Bearer <access_token>
{
  "is_published": true
}

# Delete a post (requires: delete_post permission)
DELETE /posts/{post_id}
Authorization: Bearer <access_token>
```

### Admin

```bash
# List all users with roles and permissions (requires: admin role)
GET /admin/users
Authorization: Bearer <access_token>
```

## 📝 Testing RBAC Flows

### Example 1: Viewer tries to create a post (Should fail)

```bash
# Login as viewer
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "viewer@example.com", "password": "password123"}'

# Try to create a post (will get 403 Forbidden)
curl -X POST http://localhost:8000/posts \
  -H "Authorization: Bearer <viewer_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "content": "Test content"}'

# Response: 403 Forbidden - Permission 'create_post' required
```

### Example 2: Editor creates and edits a post (Should succeed)

```bash
# Login as editor
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "editor@example.com", "password": "password123"}'

# Create a post (will succeed)
curl -X POST http://localhost:8000/posts \
  -H "Authorization: Bearer <editor_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Post", "content": "Post content"}'

# Edit the post (will succeed)
curl -X PATCH http://localhost:8000/posts/<post_id> \
  -H "Authorization: Bearer <editor_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Post"}'
```

### Example 3: Editor tries to publish a post (Should fail)

```bash
# Try to publish (will get 403 Forbidden)
curl -X POST http://localhost:8000/posts/<post_id>/publish \
  -H "Authorization: Bearer <editor_token>" \
  -H "Content-Type: application/json" \
  -d '{"is_published": true}'

# Response: 403 Forbidden - Permission 'publish_post' required
```

### Example 4: Admin publishes and deletes a post (Should succeed)

```bash
# Login as admin
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password123"}'

# Publish a post (will succeed)
curl -X POST http://localhost:8000/posts/<post_id>/publish \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"is_published": true}'

# Delete a post (will succeed)
curl -X DELETE http://localhost:8000/posts/<post_id> \
  -H "Authorization: Bearer <admin_token>"
```

## 💻 Code Walkthrough

### Protecting Routes with Permissions

```python
from fastauth.api.dependencies import require_permission

@app.post(
    "/posts",
    dependencies=[Depends(require_permission("create_post"))]
)
def create_post(post_data: PostCreate, current_user: User = Depends(get_current_user)):
    # Only users with create_post permission can access this
    # Editors and Admins have this permission
    ...
```

### Protecting Routes with Roles

```python
from fastauth.api.dependencies import require_role

@app.get(
    "/admin/users",
    dependencies=[Depends(require_role("admin"))]
)
def list_users():
    # Only users with admin role can access this
    ...
```

### Checking Permissions Programmatically

```python
from fastauth.core.roles import check_permission

def list_posts(current_user: User = Depends(get_current_user)):
    role_adapter = SQLAlchemyRoleAdapter(session)

    can_edit = check_permission(
        roles=role_adapter,
        user_id=current_user.id,
        permission_name="edit_post"
    )

    if can_edit:
        # Show all posts including drafts
        posts = session.exec(select(Post)).all()
    else:
        # Show only published posts
        posts = session.exec(select(Post).where(Post.is_published == True)).all()

    return posts
```

## 🏗️ How RBAC Works in FastAuth

### 1. Roles and Permissions are Created

```python
# Create a role
role = create_role(
    roles=role_adapter,
    name="editor",
    description="Can create and edit blog posts"
)

# Create a permission
permission = create_permission(
    roles=role_adapter,
    name="create_post",
    description="Create new blog posts"
)
```

### 2. Permissions are Assigned to Roles

```python
assign_permission_to_role(
    roles=role_adapter,
    role_name="editor",
    permission_name="create_post"
)
```

### 3. Roles are Assigned to Users

```python
assign_role(
    roles=role_adapter,
    user_id=user.id,
    role_name="editor"
)
```

### 4. Routes are Protected

```python
# Option 1: Using dependencies (declarative)
@app.post("/posts", dependencies=[Depends(require_permission("create_post"))])
def create_post():
    ...

# Option 2: Programmatic check (imperative)
def some_function():
    if check_permission(roles=role_adapter, user_id=user_id, permission_name="edit_post"):
        # User has permission
        ...
    else:
        # User doesn't have permission
        raise HTTPException(status_code=403, detail="Permission denied")
```

## 🔒 Security Features

### Permission-Based Access Control
- Routes are protected using FastAPI dependencies
- 403 Forbidden returned when user lacks required permission
- Fine-grained control over who can perform which actions

### Role-Based Access Control
- Users can have multiple roles
- Roles accumulate permissions from all assigned roles
- Easy to manage groups of permissions

### JWT Authentication
- Secure token-based authentication
- Access tokens expire after 30 minutes (configurable)
- Tokens contain user ID for permission lookups

## 🎓 Learning Resources

### Understanding RBAC Concepts

**Roles** group users with similar access needs:
- Example: "editor", "admin", "viewer"
- Users can have multiple roles

**Permissions** define specific actions:
- Example: "create_post", "delete_user", "view_analytics"
- Permissions are assigned to roles, not directly to users

**Access Control** happens at two levels:
1. **Declarative**: Using FastAPI dependencies (`require_role`, `require_permission`)
2. **Programmatic**: Using `check_permission()` function in code

### When to Use Role vs Permission

Use `require_role()` when:
- You need coarse-grained access control
- Example: Only admins can access admin dashboard

Use `require_permission()` when:
- You need fine-grained access control
- Users from different roles might have the same permission
- Example: Both editors and admins can edit posts

## 🛠️ Customization

### Adding New Roles

```python
# In app/seed.py or your own script
role = create_role(
    roles=role_adapter,
    name="moderator",
    description="Can moderate comments and posts"
)

# Assign permissions
assign_permission_to_role(
    roles=role_adapter,
    role_name="moderator",
    permission_name="edit_post"
)
```

### Adding New Permissions

```python
permission = create_permission(
    roles=role_adapter,
    name="moderate_comments",
    description="Moderate user comments"
)

# Assign to role
assign_permission_to_role(
    roles=role_adapter,
    role_name="moderator",
    permission_name="moderate_comments"
)
```

### Assigning Roles to Users

```python
from fastauth.core.roles import assign_role

assign_role(
    roles=role_adapter,
    user_id=user.id,
    role_name="moderator"
)
```

## 🐛 Troubleshooting

### "Permission required" error when it should work

**Check:**
1. User has the correct role assigned: `GET /me`
2. Role has the permission assigned: Run seed script again
3. Access token is valid and not expired: Login again

### Database already seeded

If you run the seed script multiple times, it will skip existing roles/permissions and show warnings. This is normal and safe.

### User can't see any posts

**For viewers:** Make sure posts are published (`is_published=true`)
**For editors:** Check that the user has the `edit_post` permission

## 📚 Next Steps

After understanding this example, you can:

1. **Combine with OAuth Example**: Add social login with RBAC
2. **Add More Roles**: Create custom roles for your application
3. **Implement Resource Ownership**: Check if user owns the post before allowing edits
4. **Add Audit Logging**: Track who did what and when
5. **Create Admin Dashboard**: Build a UI for managing roles and permissions

## 🤝 Contributing

Found an issue or have a suggestion? Please open an issue or PR in the main FastAuth repository.

## 📄 License

This example is part of the FastAuth project and follows the same license.
