# KiKi Shop - Korean Fashion E-commerce

A modern Django-based e-commerce platform specializing in Korean fashion for children and teens.

## 🌟 Features

### Customer Features
- **Responsive Design**: Mobile-first approach with hamburger menu and mega menu navigation
- **Product Catalog**: Browse by categories (Girls' clothes, Boys' clothes, Accessories, Baby clothes)
- **Shopping Cart**: Add to cart functionality with real-time updates
- **User Authentication**: Login, register, and profile management
- **Order Management**: Order history and tracking
- **Search Functionality**: Desktop and mobile search with filters
- **Hot Trends**: Featured trending products
- **Blog/News**: Latest fashion news and updates

### Admin Features
- **Admin Dashboard**: Complete inventory and order management
- **Staff Portal**: Staff-specific functionality
- **Content Management**: News/blog post management
- **Product Management**: Add, edit, and manage products and categories

## 🛠️ Tech Stack

- **Backend**: Django 4.x
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Database**: SQLite (development)
- **Icons**: Font Awesome 6
- **Fonts**: Google Fonts (Nunito)

## 📱 Design Features

- **Korean Fashion Theme**: Pink (#ff6b9d) and teal (#4ecdc4) color scheme
- **Responsive Navigation**: Hamburger menu with mega menu for mobile
- **Smooth Animations**: CSS transitions and hover effects
- **Modern UI**: Card-based layouts with shadows and rounded corners

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Django 4.x
- pip

### Installation

1. Clone the repository:
```bash
git clone https://github.com/WuangTX/kikishop.git
cd kikishop
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
python manage.py migrate
```

4. Create a superuser:
```bash
python manage.py createsuperuser
```

5. Run the development server:
```bash
python manage.py runserver
```

6. Visit `http://localhost:8000` to view the site

## 📁 Project Structure

```
kiki_shop/
├── admin_dashboard/          # Admin interface app
├── customer_web/            # Main customer-facing app
│   ├── templates/           # HTML templates
│   ├── static/             # CSS, JS, images
│   └── templatetags/       # Custom template filters
├── staff_portal/           # Staff management app
├── kiki_project/          # Django project settings
├── media/                 # User uploaded files
└── manage.py             # Django management script
```

## 🎨 Key Components

### Navigation
- **Desktop**: Hover-based dropdown menus
- **Mobile**: Hamburger menu with touch-friendly interactions
- **Mega Menu**: Product categories with subcategories

### Responsive Design
- **Mobile First**: Optimized for mobile devices
- **Breakpoints**: 576px, 768px, 992px
- **Flexible Layout**: Grid system with Bootstrap 5

## 🔧 Development

### Apps
- `customer_web`: Main e-commerce functionality
- `admin_dashboard`: Admin interface and management
- `staff_portal`: Staff-specific features

### Models
- Products with categories and inventory
- User profiles and authentication
- Orders and shopping cart
- News/blog posts

## 📝 License

This project is for educational and portfolio purposes.

## 👥 Contributing

This is a personal project, but suggestions and feedback are welcome!

## 📞 Contact

- **Theme**: Korean Fashion for Children
- **Target**: Modern, responsive e-commerce platform
- **Style**: Clean, colorful, user-friendly design
