import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import requests
from io import BytesIO
import random
import pygame
import os
import json

class Recipe:
    """Represents a single recipe with its details"""
    
    def __init__(self, meal_id, name, category, area, instructions, thumbnail, ingredients):
        """
        Initialize recipe object
        ARGUMENT PASSING: Constructor receives 7 arguments
        """
        self.meal_id = meal_id
        self.name = name
        self.category = category
        self.area = area
        self.instructions = instructions
        self.thumbnail = thumbnail
        self.ingredients = ingredients  # List of ingredient strings
    
    def __str__(self):
        """String representation for debugging"""
        return f"Recipe: {self.name} ({self.category})"


class MealAPI:
    """Handles all API communication with TheMealDB"""
    
    BASE_URL = "https://www.themealdb.com/api/json/v1/1"
    
    def search_by_ingredient(self, ingredient):
        """
        Search for meals by main ingredient
        ARGUMENT PASSING: Takes ingredient string as argument
        ERROR HANDLING: try-except block for network errors
        Returns: List of basic meal info or None on error
        """
        try:
            url = f"{self.BASE_URL}/filter.php?i={ingredient}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('meals'):
                return data['meals']
            else:
                return []
                
        except requests.exceptions.RequestException as e:
            # ERROR HANDLING: Catch network/API errors
            print(f"API Error: {e}")
            return None
    
    def get_recipe_details(self, meal_id):
        """
        Fetch full recipe details by meal ID
        ARGUMENT PASSING: Takes meal_id as argument, returns Recipe object
        ERROR HANDLING: try-except for API errors
        Returns: Recipe object or None on error
        """
        try:
            url = f"{self.BASE_URL}/lookup.php?i={meal_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('meals') and len(data['meals']) > 0:
                meal = data['meals'][0]
                
                # Extract ingredients
                ingredients = []
                for i in range(1, 21):
                    ingredient = meal.get(f'strIngredient{i}')
                    measure = meal.get(f'strMeasure{i}')
                    if ingredient and ingredient.strip():
                        ingredients.append(f"{measure} {ingredient}".strip())
                
                # ARGUMENT PASSING: Creating Recipe object with multiple arguments
                return Recipe(
                    meal_id=meal['idMeal'],
                    name=meal['strMeal'],
                    category=meal.get('strCategory', 'Unknown'),
                    area=meal.get('strArea', 'Unknown'),
                    instructions=meal['strInstructions'],
                    thumbnail=meal['strMealThumb'],
                    ingredients=ingredients
                )
            return None
            
        except requests.exceptions.RequestException as e:
            # ERROR HANDLING: Catch network/API errors
            print(f"API Error: {e}")
            return None
    
    def get_random_recipe(self):
        """
        Get a random recipe
        Returns: Recipe object or None on error
        """
        try:
            url = f"{self.BASE_URL}/random.php"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('meals') and len(data['meals']) > 0:
                meal = data['meals'][0]
                
                ingredients = []
                for i in range(1, 21):
                    ingredient = meal.get(f'strIngredient{i}')
                    measure = meal.get(f'strMeasure{i}')
                    if ingredient and ingredient.strip():
                        ingredients.append(f"{measure} {ingredient}".strip())
                
                return Recipe(
                    meal_id=meal['idMeal'],
                    name=meal['strMeal'],
                    category=meal.get('strCategory', 'Unknown'),
                    area=meal.get('strArea', 'Unknown'),
                    instructions=meal['strInstructions'],
                    thumbnail=meal['strMealThumb'],
                    ingredients=ingredients
                )
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return None

class ChefApp:
    """Main application class for the Recipe Finder GUI"""
    
    def __init__(self, root):
        """
        Initialize the GUI application
        ARGUMENT PASSING: Takes root Tkinter window as argument
        """
        self.root = root
        self.root.title("Recipe Finder Application")
        self.root.geometry("800x600")
        
        # Modern color scheme - vibrant and alive!
        self.colors = {
            'bg': '#F5F7FA',
            'primary': '#6C5CE7',
            'secondary': '#FD79A8',
            'success': '#00B894',
            'warning': '#FDCB6E',
            'card': '#FFFFFF',
            'text_dark': '#2D3436',
            'text_light': '#636E72',
            'accent': '#FF6B6B',
            'avatar_bg': '#A29BFE',
            'dialogue_bg': '#DFE6E9',
            'bar': '#74B9FF'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Create images cache directory
        self.images_dir = "images"
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
        
        # Initialize pygame mixer for music
        pygame.mixer.init()
        
        # Download and setup jazz music
        self.setup_music()
        
        # OOP: Create instance of MealAPI class
        self.api = MealAPI()
        
        # Store current recipes list
        self.current_recipes = []
        self.all_recipes = []  # Store unfiltered recipes
        self.recipe_images = {}  # Store PhotoImage objects
        
        # Music state
        self.music_playing = True
        
        # Filter variables (initialize before creating frames)
        self.filter_chicken = tk.BooleanVar(value=False)
        self.filter_beef = tk.BooleanVar(value=False)
        self.filter_seafood = tk.BooleanVar(value=False)
        
        # Create main container
        self.main_container = tk.Frame(self.root, bg=self.colors['bg'])
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create frames
        self.create_welcome_frame()
        self.create_instruction_frame()
        self.create_main_frame()
        self.create_detail_frame()
        
        # Show welcome frame initially
        self.show_frame("welcome")
    
    def setup_music(self):
        """Load and play local jazz restaurant background music"""
        try:
            # Use relative path - looks for music file in same directory as script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            music_path = os.path.join(script_dir, "Restaurant_jazz.mp3")
            
            # Check if music file exists
            if not os.path.exists(music_path):
                print("Warning: Restaurant_jazz.mp3 not found. Running without music.")
                print(f"Expected location: {music_path}")
                print("To add music: Download a jazz MP3 and save it as 'Restaurant_jazz.mp3' in the same folder as this script.")
                return
            
            # Load and play the music
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(0.3)  # Set to 30% volume for background
            pygame.mixer.music.play(-1)  # Loop indefinitely
            print("Jazz music loaded successfully!")
            
        except Exception as e:
            print(f"Could not load music: {e}")
            # Continue without music if it fails
    
    def load_recipe_cache(self, meal_id):
        """Load recipe data from cache if available"""
        cache_file = os.path.join(self.images_dir, f"{meal_id}_recipe.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    return Recipe(
                        meal_id=data['meal_id'],
                        name=data['name'],
                        category=data['category'],
                        area=data['area'],
                        instructions=data['instructions'],
                        thumbnail=data['thumbnail'],
                        ingredients=data['ingredients']
                    )
            except:
                return None
        return None
    
    def save_recipe_cache(self, recipe):
        """Save recipe data to cache"""
        cache_file = os.path.join(self.images_dir, f"{recipe.meal_id}_recipe.json")
        try:
            data = {
                'meal_id': recipe.meal_id,
                'name': recipe.name,
                'category': recipe.category,
                'area': recipe.area,
                'instructions': recipe.instructions,
                'thumbnail': recipe.thumbnail,
                'ingredients': recipe.ingredients
            }
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def load_image_cached(self, url, meal_id, width, height):
        """
        Load image from cache or download if not cached
        Returns PIL ImageTk.PhotoImage object
        """
        # Create filename based on meal_id
        cache_filename = os.path.join(self.images_dir, f"{meal_id}.jpg")
        
        try:
            # Check if image exists in cache
            if os.path.exists(cache_filename):
                # Load from cache
                img_data = Image.open(cache_filename)
            else:
                # Download and save to cache
                response = requests.get(url, timeout=5)
                img_data = Image.open(BytesIO(response.content))
                # Save to cache
                img_data.save(cache_filename, "JPEG")
            
            # Resize and return
            img_data = img_data.resize((width, height), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img_data)
            
        except Exception as e:
            print(f"Error loading image: {e}")
            return None
    
    def create_welcome_frame(self):
        """Create the welcome screen frame"""
        self.welcome_frame = tk.Frame(self.main_container, bg='#2D3436')
        
        # Center container
        center_container = tk.Frame(self.welcome_frame, bg='#2D3436')
        center_container.place(relx=0.5, rely=0.5, anchor='center')
        
        # Title
        tk.Label(
            center_container,
            text="🍳 Recipe Finder 🍳",
            font=("Segoe UI", 40, "bold"),
            bg='#2D3436',
            fg='white'
        ).pack(pady=(0, 80))
        
        # Button container
        button_container = tk.Frame(center_container, bg='#2D3436')
        button_container.pack()
        
        # Instruction button
        instruction_btn = tk.Button(
            button_container,
            text="Instructions",
            font=("Segoe UI", 14),
            bg='#2D3436',
            fg='#74B9FF',
            cursor="hand2",
            relief=tk.FLAT,
            command=lambda: self.show_frame("instruction"),
            width=15,
            height=2,
            borderwidth=2,
            highlightthickness=2,
            highlightbackground='#74B9FF',
            highlightcolor='#74B9FF',
            activebackground='#74B9FF',
            activeforeground='white'
        )
        instruction_btn.pack(side=tk.LEFT, padx=20)
        
        # Continue button
        continue_btn = tk.Button(
            button_container,
            text="Continue",
            font=("Segoe UI", 14),
            bg='#2D3436',
            fg='#74B9FF',
            cursor="hand2",
            relief=tk.FLAT,
            command=lambda: self.show_frame("main"),
            width=15,
            height=2,
            borderwidth=2,
            highlightthickness=2,
            highlightbackground='#74B9FF',
            highlightcolor='#74B9FF',
            activebackground='#74B9FF',
            activeforeground='white'
        )
        continue_btn.pack(side=tk.LEFT, padx=20)
        
        # Hover effects
        def on_enter_inst(e):
            instruction_btn.config(bg='#74B9FF', fg='white')
        def on_leave_inst(e):
            instruction_btn.config(bg='#2D3436', fg='#74B9FF')
        
        def on_enter_cont(e):
            continue_btn.config(bg='#74B9FF', fg='white')
        def on_leave_cont(e):
            continue_btn.config(bg='#2D3436', fg='#74B9FF')
        
        instruction_btn.bind("<Enter>", on_enter_inst)
        instruction_btn.bind("<Leave>", on_leave_inst)
        continue_btn.bind("<Enter>", on_enter_cont)
        continue_btn.bind("<Leave>", on_leave_cont)
    
    def create_instruction_frame(self):
        """Create the instruction screen frame"""
        self.instruction_frame = tk.Frame(self.main_container, bg='#2D3436')
        
        # Center container
        center_container = tk.Frame(self.instruction_frame, bg='#2D3436')
        center_container.place(relx=0.5, rely=0.5, anchor='center')
        
        # Title
        tk.Label(
            center_container,
            text="Instructions",
            font=("Segoe UI", 36, "bold"),
            bg='#2D3436',
            fg='white'
        ).pack(pady=(0, 40))
        
        # Instructions text
        instructions = [
            "Greetings! Welcome to Recipe Finder, an application used for viewing",
            "several recipes inside the TheMealDB API, which you can find here:",
            "https://www.themealdb.com/",
            "",
            "Mouse controls are used to navigate. Click the continue button to begin.",
            "Have fun!"
        ]
        
        for line in instructions:
            tk.Label(
                center_container,
                text=line,
                font=("Segoe UI", 12),
                bg='#2D3436',
                fg='#B2BEC3'
            ).pack(pady=3)
        
        # Continue button
        continue_btn = tk.Button(
            center_container,
            text="Continue",
            font=("Segoe UI", 14),
            bg='#2D3436',
            fg='#74B9FF',
            cursor="hand2",
            relief=tk.FLAT,
            command=lambda: self.show_frame("main"),
            width=15,
            height=2,
            borderwidth=2,
            highlightthickness=2,
            highlightbackground='#74B9FF',
            highlightcolor='#74B9FF',
            activebackground='#74B9FF',
            activeforeground='white'
        )
        continue_btn.pack(pady=40)
        
        # Hover effect
        def on_enter(e):
            continue_btn.config(bg='#74B9FF', fg='white')
        def on_leave(e):
            continue_btn.config(bg='#2D3436', fg='#74B9FF')
        
        continue_btn.bind("<Enter>", on_enter)
        continue_btn.bind("<Leave>", on_leave)
    
    def create_main_frame(self):
        """Create the main view frame with recipe cards"""
        self.main_frame = tk.Frame(self.main_container, bg=self.colors['bg'])
        
        # Top section - Title and menu
        top_section = tk.Frame(self.main_frame, bg=self.colors['bg'])
        top_section.pack(fill=tk.X, padx=20, pady=20)
        
        # Left side - Title and menu
        left_section = tk.Frame(top_section, bg=self.colors['bg'])
        left_section.pack(side=tk.LEFT, fill=tk.Y)
        
        tk.Label(
            left_section,
            text="🍳 Recipe Finder",
            font=("Segoe UI", 20, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['primary']
        ).pack(anchor=tk.W, pady=(0, 15))
        
        # Menu items with better styling
        menu_items = [
            ("• View All Recipe", self.view_all_recipes, self.colors['primary']),
            ("• Get Random Recipe", self.get_random_recipe, self.colors['secondary']),
            ("• Get Specific Recipe", self.show_search_dialog, self.colors['success']),
            ("• Filter Recipe", self.show_search_dialog, self.colors['warning'])
        ]
        
        for text, command, color in menu_items:
            btn = tk.Button(
                left_section,
                text=text,
                font=("Segoe UI", 11),
                bg=self.colors['card'],
                fg=color,
                anchor="w",
                relief=tk.FLAT,
                cursor="hand2",
                command=command,
                width=20,
                borderwidth=2,
                highlightthickness=2,
                highlightbackground=color,
                highlightcolor=color,
                activebackground=color,
                activeforeground='white'
            )
            btn.pack(anchor=tk.W, pady=4)
            
            # Add hover effect
            def on_enter(e, b=btn, c=color):
                b.config(bg=c, fg='white')
            def on_leave(e, b=btn, c=color):
                b.config(bg=self.colors['card'], fg=c)
            
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
        
        # Category checkboxes
        tk.Label(
            left_section,
            text="Filter by:",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['text_dark']
        ).pack(pady=(10, 5), anchor=tk.W)
        
        filter_frame = tk.Frame(left_section, bg=self.colors['bg'])
        filter_frame.pack(anchor=tk.W)
        
        tk.Checkbutton(
            filter_frame, 
            text="Chicken", 
            bg=self.colors['bg'], 
            font=("Segoe UI", 9),
            variable=self.filter_chicken,
            command=self.apply_filters,
            fg=self.colors['text_dark'],
            activebackground=self.colors['bg'],
            selectcolor='white'
        ).pack(anchor=tk.W, pady=2)
        
        tk.Checkbutton(
            filter_frame, 
            text="Beef", 
            bg=self.colors['bg'], 
            font=("Segoe UI", 9),
            variable=self.filter_beef,
            command=self.apply_filters,
            fg=self.colors['text_dark'],
            activebackground=self.colors['bg'],
            selectcolor='white'
        ).pack(anchor=tk.W, pady=2)
        
        tk.Checkbutton(
            filter_frame, 
            text="Seafood", 
            bg=self.colors['bg'], 
            font=("Segoe UI", 9),
            variable=self.filter_seafood,
            command=self.apply_filters,
            fg=self.colors['text_dark'],
            activebackground=self.colors['bg'],
            selectcolor='white'
        ).pack(anchor=tk.W, pady=2)
        
        
        # Right side - Avatar and dialogue with gradient effect
        right_section = tk.Frame(top_section, bg=self.colors['bg'])
        right_section.pack(side=tk.RIGHT, padx=50)
        
        avatar_dialogue = tk.Frame(right_section, bg=self.colors['bg'])
        avatar_dialogue.pack()
        
        # Avatar with better styling
        avatar_canvas = tk.Canvas(avatar_dialogue, width=100, height=100, bg=self.colors['bg'], highlightthickness=0)
        avatar_canvas.pack(side=tk.LEFT, padx=10)
        
        # Draw a colorful avatar (larger size)
        avatar_canvas.create_oval(5, 5, 95, 95, fill=self.colors['avatar_bg'], outline=self.colors['primary'], width=4)
        # Chef hat
        avatar_canvas.create_oval(25, 15, 75, 45, fill='white', outline='white')
        avatar_canvas.create_rectangle(30, 40, 70, 60, fill='white', outline='white')
        # Eyes
        avatar_canvas.create_oval(35, 50, 45, 60, fill=self.colors['text_dark'])
        avatar_canvas.create_oval(55, 50, 65, 60, fill=self.colors['text_dark'])
        # Smile
        avatar_canvas.create_arc(35, 60, 65, 80, start=0, extent=-180, style=tk.ARC, width=3, outline=self.colors['text_dark'])
        
        # Dialogue bubble with shadow effect
        dialogue_shadow = tk.Frame(avatar_dialogue, bg='#B0B0B0')
        dialogue_shadow.place(x=92, y=2)
        
        dialogue_frame = tk.Frame(avatar_dialogue, bg='white', relief=tk.RAISED, bd=0, 
                                 highlightbackground=self.colors['primary'], highlightthickness=2)
        dialogue_frame.pack(side=tk.LEFT)
        
        self.dialogue_label = tk.Label(
            dialogue_frame,
            text="Welcome! What are\nyou having today? 😊",
            font=("Segoe UI", 11),
            bg='white',
            fg=self.colors['text_dark'],
            justify=tk.LEFT
        )
        self.dialogue_label.pack(padx=15, pady=10)
        
        tk.Label(
            dialogue_frame,
            text="",
            font=("Segoe UI", 8, "italic"),
            bg='white',
            fg=self.colors['text_light']
        ).pack(padx=10, pady=(0, 8))
        
        # Colorful bar below menu
        bar_canvas = tk.Canvas(self.main_frame, bg=self.colors['bg'], height=60, highlightthickness=0)
        bar_canvas.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Create gradient bar
        for i in range(800):
            color_ratio = i / 800
            r = int(116 + (253 - 116) * color_ratio)
            g = int(185 + (121 - 185) * color_ratio)
            b = int(255 + (168 - 255) * color_ratio)
            color = f'#{r:02x}{g:02x}{b:02x}'
            bar_canvas.create_line(i, 0, i, 60, fill=color, width=1)
        
        bar_canvas.create_text(400, 30, text="✨ Delicious Recipes Await ✨", 
                              font=("Segoe UI", 14, "bold"), fill='white')
        
        # Recipe cards area with canvas for scrolling
        cards_container = tk.Frame(self.main_frame, bg=self.colors['bg'])
        cards_container.pack(fill=tk.BOTH, expand=True, padx=20)
        
        self.canvas = tk.Canvas(cards_container, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(cards_container, orient=tk.VERTICAL, command=self.canvas.yview,
                                bg=self.colors['primary'], troughcolor=self.colors['bg'],
                                activebackground=self.colors['secondary'])
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.colors['bg'])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mute Music button at bottom right with better styling
        bottom_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.music_btn_main = tk.Button(
            bottom_frame,
            text="🔇 Mute Music",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['accent'],
            fg='white',
            cursor="hand2",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            activebackground=self.colors['secondary'],
            command=self.toggle_music
        )
        self.music_btn_main.pack(side=tk.RIGHT, padx=20, pady=10)
        
        def music_hover_enter(e):
            self.music_btn_main.config(bg=self.colors['secondary'])
        def music_hover_leave(e):
            self.music_btn_main.config(bg=self.colors['accent'])
        
        self.music_btn_main.bind("<Enter>", music_hover_enter)
        self.music_btn_main.bind("<Leave>", music_hover_leave)
    
    def create_detail_frame(self):
        """Create the detail view frame for showing full recipe"""
        self.detail_frame = tk.Frame(self.main_container, bg=self.colors['bg'])
        
        # Top section
        top_section = tk.Frame(self.detail_frame, bg=self.colors['bg'])
        top_section.pack(fill=tk.X, padx=20, pady=20)
        
        # Left side - Title and menu
        left_section = tk.Frame(top_section, bg=self.colors['bg'])
        left_section.pack(side=tk.LEFT, fill=tk.Y)
        
        tk.Label(
            left_section,
            text="🍳 Recipe Finder",
            font=("Segoe UI", 20, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['primary']
        ).pack(anchor=tk.W, pady=(0, 15))
        
        # Menu items with colors
        menu_items = [
            ("• View All Recipe", lambda: self.show_frame("main"), self.colors['primary']),
            ("• Get Random Recipe", self.get_random_recipe, self.colors['secondary']),
            ("• Get Specific Recipe", self.show_search_dialog, self.colors['success']),
            ("• Filter Recipe", self.show_search_dialog, self.colors['warning'])
        ]
        
        for text, command, color in menu_items:
            btn = tk.Button(
                left_section,
                text=text,
                font=("Segoe UI", 11),
                bg=self.colors['card'],
                fg=color,
                anchor="w",
                relief=tk.FLAT,
                cursor="hand2",
                command=command,
                width=20,
                borderwidth=2,
                highlightthickness=2,
                highlightbackground=color,
                highlightcolor=color,
                activebackground=color,
                activeforeground='white'
            )
            btn.pack(anchor=tk.W, pady=4)
            
            # Add hover effect
            def on_enter(e, b=btn, c=color):
                b.config(bg=c, fg='white')
            def on_leave(e, b=btn, c=color):
                b.config(bg=self.colors['card'], fg=c)
            
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
        
        # Category checkboxes
        tk.Label(left_section, text="Filter by:", font=("Segoe UI", 10, "bold"),
                bg=self.colors['bg'], fg=self.colors['text_dark']).pack(pady=(10, 5), anchor=tk.W)
        
        filter_frame = tk.Frame(left_section, bg=self.colors['bg'])
        filter_frame.pack(anchor=tk.W)
        
        tk.Checkbutton(filter_frame, text="Chicken", bg=self.colors['bg'], 
                      font=("Segoe UI", 9), fg=self.colors['text_dark'],
                      variable=self.filter_chicken,
                      command=self.apply_filters,
                      activebackground=self.colors['bg'],
                      selectcolor='white').pack(anchor=tk.W, pady=2)
        tk.Checkbutton(filter_frame, text="Beef", bg=self.colors['bg'], 
                      font=("Segoe UI", 9), fg=self.colors['text_dark'],
                      variable=self.filter_beef,
                      command=self.apply_filters,
                      activebackground=self.colors['bg'],
                      selectcolor='white').pack(anchor=tk.W, pady=2)
        tk.Checkbutton(filter_frame, text="Seafood", bg=self.colors['bg'], 
                      font=("Segoe UI", 9), fg=self.colors['text_dark'],
                      variable=self.filter_seafood,
                      command=self.apply_filters,
                      activebackground=self.colors['bg'],
                      selectcolor='white').pack(anchor=tk.W, pady=2)
        
        # Right side - Avatar and dialogue
        right_section = tk.Frame(top_section, bg=self.colors['bg'])
        right_section.pack(side=tk.RIGHT, padx=50)
        
        avatar_dialogue = tk.Frame(right_section, bg=self.colors['bg'])
        avatar_dialogue.pack()
        
        # Avatar
        avatar_canvas = tk.Canvas(avatar_dialogue, width=100, height=100, bg=self.colors['bg'], highlightthickness=0)
        avatar_canvas.pack(side=tk.LEFT, padx=10)
        
        # Draw colorful avatar (larger size)
        avatar_canvas.create_oval(5, 5, 95, 95, fill=self.colors['avatar_bg'], outline=self.colors['primary'], width=4)
        avatar_canvas.create_oval(25, 15, 75, 45, fill='white', outline='white')
        avatar_canvas.create_rectangle(30, 40, 70, 60, fill='white', outline='white')
        avatar_canvas.create_oval(35, 50, 45, 60, fill=self.colors['text_dark'])
        avatar_canvas.create_oval(55, 50, 65, 60, fill=self.colors['text_dark'])
        avatar_canvas.create_arc(35, 60, 65, 80, start=0, extent=-180, style=tk.ARC, width=3, outline=self.colors['text_dark'])
        
        # Dialogue bubble
        dialogue_frame = tk.Frame(avatar_dialogue, bg='white', relief=tk.RAISED, bd=0,
                                 highlightbackground=self.colors['primary'], highlightthickness=2)
        dialogue_frame.pack(side=tk.LEFT)
        
        tk.Label(
            dialogue_frame,
            text="Enjoy this special\nrecipe today! 🎉",
            font=("Segoe UI", 11),
            bg='white',
            fg=self.colors['text_dark'],
            justify=tk.LEFT
        ).pack(padx=15, pady=10)
        
        tk.Label(
            dialogue_frame,
            text="",
            font=("Segoe UI", 8, "italic"),
            bg='white',
            fg=self.colors['text_light']
        ).pack(padx=10, pady=(0, 8))
        
        # Colorful bar
        bar_canvas = tk.Canvas(self.detail_frame, bg=self.colors['bg'], height=60, highlightthickness=0)
        bar_canvas.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        for i in range(800):
            color_ratio = i / 800
            r = int(116 + (253 - 116) * color_ratio)
            g = int(185 + (121 - 185) * color_ratio)
            b = int(255 + (168 - 255) * color_ratio)
            color = f'#{r:02x}{g:02x}{b:02x}'
            bar_canvas.create_line(i, 0, i, 60, fill=color, width=1)
        
        bar_canvas.create_text(400, 30, text="📖 Recipe Details", 
                              font=("Segoe UI", 14, "bold"), fill='white')
        
        # Detail content area
        detail_content = tk.Frame(self.detail_frame, bg='white', relief=tk.FLAT,
                                 highlightbackground=self.colors['primary'], highlightthickness=2)
        detail_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Left side - Image and info
        left_detail = tk.Frame(detail_content, bg='white')
        left_detail.pack(side=tk.LEFT, padx=20, pady=20)
        
        # Recipe image with border
        image_border = tk.Frame(left_detail, bg=self.colors['primary'], padx=3, pady=3)
        image_border.pack(pady=(0, 15))
        
        self.detail_image_label = tk.Label(image_border, bg='#f0f0f0', width=150, height=150)
        self.detail_image_label.pack()
        
        # Recipe info labels with better styling
        info_frame = tk.Frame(left_detail, bg='white')
        info_frame.pack()
        
        self.detail_name_label = tk.Label(
            info_frame,
            text="Recipe Name",
            font=("Segoe UI", 12, "bold"),
            bg='white',
            fg=self.colors['primary'],
            anchor="w"
        )
        self.detail_name_label.pack(anchor="w", pady=3)
        
        self.detail_category_label = tk.Label(
            info_frame,
            text="Category",
            font=("Segoe UI", 10),
            bg='white',
            fg=self.colors['text_dark'],
            anchor="w"
        )
        self.detail_category_label.pack(anchor="w", pady=2)
        
        self.detail_area_label = tk.Label(
            info_frame,
            text="Cuisine",
            font=("Segoe UI", 10),
            bg='white',
            fg=self.colors['text_dark'],
            anchor="w"
        )
        self.detail_area_label.pack(anchor="w", pady=2)
        
        # Right side - Ingredients
        right_detail = tk.Frame(detail_content, bg='white')
        right_detail.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(
            right_detail,
            text="🥘 Ingredients:",
            font=("Segoe UI", 12, "bold"),
            bg='white',
            fg=self.colors['secondary']
        ).pack(anchor="w", pady=(0, 10))
        
        # Ingredients display area
        ingredients_container = tk.Frame(right_detail, bg='white')
        ingredients_container.pack(fill=tk.BOTH, expand=True)
        
        # Two columns for ingredients
        self.ingredients_col1 = tk.Frame(ingredients_container, bg='white')
        self.ingredients_col1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.ingredients_col2 = tk.Frame(ingredients_container, bg='white')
        self.ingredients_col2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Arrow and Mute Music at bottom
        bottom_frame = tk.Frame(self.detail_frame, bg=self.colors['bg'])
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        tk.Label(bottom_frame, text="▶", font=("Arial", 16), bg=self.colors['bg'], 
                fg=self.colors['primary']).pack(side=tk.RIGHT, padx=5)
        
        self.music_btn_detail = tk.Button(
            bottom_frame,
            text="🔇 Mute Music",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['accent'],
            fg='white',
            cursor="hand2",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            activebackground=self.colors['secondary'],
            command=self.toggle_music
        )
        self.music_btn_detail.pack(side=tk.RIGHT, padx=20, pady=10)
        
        def music_hover_enter(e):
            self.music_btn_detail.config(bg=self.colors['secondary'])
        def music_hover_leave(e):
            self.music_btn_detail.config(bg=self.colors['accent'])
        
        self.music_btn_detail.bind("<Enter>", music_hover_enter)
        self.music_btn_detail.bind("<Leave>", music_hover_leave)
    
    def show_frame(self, frame_name):
        """
        Show a specific frame
        ARGUMENT PASSING: Takes frame name as argument
        """
        # Hide all frames
        self.welcome_frame.pack_forget()
        self.instruction_frame.pack_forget()
        self.main_frame.pack_forget()
        self.detail_frame.pack_forget()
        
        # Show requested frame
        if frame_name == "welcome":
            self.welcome_frame.pack(fill=tk.BOTH, expand=True)
        elif frame_name == "instruction":
            self.instruction_frame.pack(fill=tk.BOTH, expand=True)
        elif frame_name == "main":
            self.main_frame.pack(fill=tk.BOTH, expand=True)
        else:  # detail
            self.detail_frame.pack(fill=tk.BOTH, expand=True)
    
    def show_search_dialog(self):
        """
        Show search dialog for ingredient input
        KEYBOARD INPUT REQUIREMENT: Entry widget in dialog
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("Search Recipes")
        dialog.geometry("400x180")
        dialog.configure(bg='white')
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(
            dialog,
            text="🔍 Enter an ingredient to search:",
            font=("Segoe UI", 12, "bold"),
            bg='white',
            fg=self.colors['primary']
        ).pack(pady=20)
        
        # Entry widget with styling
        entry_frame = tk.Frame(dialog, bg='white')
        entry_frame.pack(pady=10)
        
        entry = tk.Entry(entry_frame, font=("Segoe UI", 12), width=30,
                        relief=tk.FLAT, borderwidth=2,
                        highlightthickness=2, highlightbackground=self.colors['primary'],
                        highlightcolor=self.colors['secondary'])
        entry.pack(ipady=5, padx=2, pady=2)
        entry.focus()
        
        def do_search():
            ingredient = entry.get().strip()
            if not ingredient:
                messagebox.showerror("Error", "Please enter an ingredient to search!")
                return
            dialog.destroy()
            self.search_recipes(ingredient)
        
        entry.bind('<Return>', lambda e: do_search())
        
        search_btn = tk.Button(
            dialog,
            text="Search 🔍",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['success'],
            fg="white",
            cursor="hand2",
            command=do_search,
            relief=tk.FLAT,
            padx=30,
            pady=10,
            activebackground=self.colors['primary']
        )
        search_btn.pack(pady=10)
        
        def btn_hover_enter(e):
            search_btn.config(bg=self.colors['primary'])
        def btn_hover_leave(e):
            search_btn.config(bg=self.colors['success'])
        
        search_btn.bind("<Enter>", btn_hover_enter)
        search_btn.bind("<Leave>", btn_hover_leave)
    
    def search_recipes(self, ingredient):
        """
        Search for recipes by ingredient
        ARGUMENT PASSING: Takes ingredient string as argument
        """
        # Update bartender dialogue
        self.dialogue_label.config(text="Searching for\ndelicious recipes! 🔍")
        self.root.update()
        
        # Pass ingredient to API method
        results = self.api.search_by_ingredient(ingredient)
        
        # Check if API call failed
        if results is None:
            messagebox.showerror(
                "Connection Error",
                "Could not connect to recipe database. Check your internet connection."
            )
            self.dialogue_label.config(text="Oops! Connection\nerror 😞")
            return
        
        if len(results) == 0:
            messagebox.showinfo("No Results", f"No recipes found for '{ingredient}'")
            self.dialogue_label.config(text="No recipes found\nTry another! 🤔")
            return
        
        # Fetch full details for each recipe
        self.all_recipes = []
        for meal in results[:10]:  # Limit to 10 recipes
            # Try to load from cache first
            recipe = self.load_recipe_cache(meal['idMeal'])
            
            # If not in cache, fetch from API
            if not recipe:
                recipe = self.api.get_recipe_details(meal['idMeal'])
                if recipe:
                    # Save to cache for next time
                    self.save_recipe_cache(recipe)
            
            if recipe:
                self.all_recipes.append(recipe)
        
        # Apply filters
        self.apply_filters()
        
        # Update dialogue
        self.dialogue_label.config(text=f"Found {len(self.current_recipes)}\nrecipes! 🎉")
    
    def apply_filters(self):
        """Apply selected filters to the recipe list"""
        if not self.all_recipes:
            return
        
        # If no filters selected, show all
        if not (self.filter_chicken.get() or self.filter_beef.get() or self.filter_seafood.get()):
            self.current_recipes = self.all_recipes[:]
        else:
            # Filter based on category or name containing the protein
            self.current_recipes = []
            for recipe in self.all_recipes:
                category_lower = recipe.category.lower()
                name_lower = recipe.name.lower()
                
                if self.filter_chicken.get() and ("chicken" in category_lower or "chicken" in name_lower):
                    self.current_recipes.append(recipe)
                elif self.filter_beef.get() and ("beef" in category_lower or "beef" in name_lower):
                    self.current_recipes.append(recipe)
                elif self.filter_seafood.get() and ("seafood" in category_lower or "fish" in name_lower or "prawn" in name_lower or "salmon" in name_lower):
                    self.current_recipes.append(recipe)
        
        self.display_recipe_cards()
        
        # Update dialogue
        if self.current_recipes:
            self.dialogue_label.config(text=f"Filtered to\n{len(self.current_recipes)} recipes! 🎯")
        else:
            self.dialogue_label.config(text="No matches\nfor that filter 🤔")
    
    def toggle_music(self):
        self.music_playing = not self.music_playing
        
        if self.music_playing:
            # Music is now playing
            pygame.mixer.music.unpause()
            self.music_btn_main.config(text="🔇 Mute Music")
            self.music_btn_detail.config(text="🔇 Mute Music")
            self.dialogue_label.config(text="Enjoying the\nmusic! 🎵")
        else:
            # Music is now muted
            pygame.mixer.music.pause()
            self.music_btn_main.config(text="🔊 Play Music")
            self.music_btn_detail.config(text="🔊 Play Music")
            self.dialogue_label.config(text="Music paused.\nSo quiet... 🤫")
    
    def view_all_recipes(self):
        """View all recipes - fetch 3 chicken, 3 beef, and 3 seafood"""
        self.dialogue_label.config(text="Loading all\nrecipes! 📚")
        self.root.update()
        
        self.all_recipes = []
        ingredients = ["chicken", "beef", "salmon"]
        
        for ingredient in ingredients:
            results = self.api.search_by_ingredient(ingredient)
            if results:
                for meal in results[:3]:
                    # Try to load from cache first
                    recipe = self.load_recipe_cache(meal['idMeal'])
                    
                    # If not in cache, fetch from API
                    if not recipe:
                        recipe = self.api.get_recipe_details(meal['idMeal'])
                        if recipe:
                            # Save to cache for next time
                            self.save_recipe_cache(recipe)
                    
                    if recipe:
                        self.all_recipes.append(recipe)
                        self.dialogue_label.config(text=f"Loading...\n{len(self.all_recipes)}/9")
                        self.root.update()
        
        self.apply_filters()
        self.dialogue_label.config(text=f"Found {len(self.current_recipes)}\nrecipes! 🎉")
    
    def get_random_recipe(self):
        """Get a random recipe and show it"""
        self.dialogue_label.config(text="Feeling lucky?\nLet's see! 🎲")
        self.root.update()
        
        recipe = self.api.get_random_recipe()
        
        if recipe is None:
            messagebox.showerror("Error", "Could not fetch random recipe. Check your connection.")
            self.dialogue_label.config(text="Oops! Try\nagain 😞")
            return
        
        # Pass Recipe object to detail view
        self.dialogue_label.config(text="Here's a surprise\nfor you! ✨")
        self.show_recipe_detail(recipe)
    
    def display_recipe_cards(self):
        """Display recipe cards in grid layout"""
        # Clear previous cards
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Create grid of cards (5 per row)
        for idx, recipe in enumerate(self.current_recipes):
            row = idx // 5
            col = idx % 5
            
            card = self.create_recipe_card(self.scrollable_frame, recipe)
            card.grid(row=row, column=col, padx=10, pady=10)
    
    def create_recipe_card(self, parent, recipe):
        """
        Create a recipe card widget
        ARGUMENT PASSING: Takes parent widget and Recipe object as arguments
        MOUSE INTERACTION: Click to view details
        """
        # Random color for each card
        colors = [self.colors['primary'], self.colors['secondary'], self.colors['success'], 
                 self.colors['warning'], self.colors['accent']]
        card_color = colors[hash(recipe.meal_id) % len(colors)]
        
        card_frame = tk.Frame(parent, bg='white', width=130, height=150, relief=tk.FLAT, bd=0,
                             highlightbackground=card_color, highlightthickness=3)
        card_frame.pack_propagate(False)
        
        # Image placeholder
        image_label = tk.Label(card_frame, bg='#f5f5f5')
        image_label.pack(pady=(5, 5), padx=5)
        
        # Load image using cache system
        photo = self.load_image_cached(recipe.thumbnail, recipe.meal_id, 120, 90)
        if photo:
            image_label.config(image=photo, width=120, height=90)
            image_label.image = photo
            self.recipe_images[recipe.meal_id] = photo
        else:
            image_label.config(width=120, height=90)
        
        # Recipe name with color
        name_label = tk.Label(
            card_frame,
            text=recipe.name[:18] + "..." if len(recipe.name) > 18 else recipe.name,
            font=("Segoe UI", 9, "bold"),
            bg='white',
            fg=card_color,
            wraplength=120
        )
        name_label.pack(pady=(0, 5))
        # Click event to show detail
        card_frame.bind("<Button-1>", lambda e, r=recipe: self.show_recipe_detail(r))
        image_label.bind("<Button-1>", lambda e, r=recipe: self.show_recipe_detail(r))
        name_label.bind("<Button-1>", lambda e, r=recipe: self.show_recipe_detail(r))
        
        # Hover effects
        def on_enter(e):
            card_frame.config(highlightthickness=5)
            name_label.config(font=("Segoe UI", 9, "bold underline"))
        
        def on_leave(e):
            card_frame.config(highlightthickness=3)
            name_label.config(font=("Segoe UI", 9, "bold"))
        
        card_frame.bind("<Enter>", on_enter)
        card_frame.bind("<Leave>", on_leave)
        
        # Change cursor on hover
        card_frame.config(cursor="hand2")
        image_label.config(cursor="hand2")
        name_label.config(cursor="hand2")
        
        return card_frame
    
    def show_recipe_detail(self, recipe):
        # Update bartender dialogue
        dialogues = [
            "This looks\ndelicious! 😋",
            "A great choice!\nEnjoy! 🍽️",
            "Time to cook!\nLet's go! 👨‍🍳",
            "Yummy! This is\none of my favs! ⭐"
        ]
        self.dialogue_label.config(text=random.choice(dialogues))
        
        # Update detail frame with recipe info
        self.detail_name_label.config(text=recipe.name)
        self.detail_category_label.config(text=f"📁 {recipe.category}")
        self.detail_area_label.config(text=f"🌍 {recipe.area}")
        
        # Load recipe image using cache system
        photo = self.load_image_cached(recipe.thumbnail, recipe.meal_id, 150, 150)
        if photo:
            self.detail_image_label.config(image=photo)
            self.detail_image_label.image = photo
        else:
            self.detail_image_label.config(image="", text="No Image")
        
        # Display ingredients in two columns with emojis
        for widget in self.ingredients_col1.winfo_children():
            widget.destroy()
        for widget in self.ingredients_col2.winfo_children():
            widget.destroy()
        
        mid = len(recipe.ingredients) // 2
        for i, ingredient in enumerate(recipe.ingredients):
            emoji = "✓"
            color = self.colors['success']
            
            if i < mid:
                ing_frame = tk.Frame(self.ingredients_col1, bg='white')
                ing_frame.pack(fill=tk.X, pady=2, anchor="w")
            else:
                ing_frame = tk.Frame(self.ingredients_col2, bg='white')
                ing_frame.pack(fill=tk.X, pady=2, anchor="w")
            
            tk.Label(
                ing_frame,
                text=emoji,
                font=("Segoe UI", 9, "bold"),
                bg='white',
                fg=color
            ).pack(side=tk.LEFT, padx=(0, 5))
            
            tk.Label(
                ing_frame,
                text=ingredient,
                font=("Segoe UI", 9),
                bg='white',
                fg=self.colors['text_dark'],
                anchor="w"
            ).pack(side=tk.LEFT, fill=tk.X)
        
        # Show detail frame
        self.show_frame("detail")

if __name__ == "__main__":
    # Create main window
    root = tk.Tk()
    
    # OOP: Create instance of ChefApp class
    # ARGUMENT PASSING: Pass root window to constructor
    app = ChefApp(root)
    
    # Start GUI event loop
    root.mainloop()