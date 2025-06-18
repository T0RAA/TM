import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import Callable, List, Dict, Any

class SpotifySearchDropdown:
    def __init__(self, parent, search_function: Callable[[str], List[Dict[str, Any]]], 
                 placeholder: str = "Search...", width: int = 30, max_results: int = 10):
        """
        Initialize the Spotify search dropdown
        
        Args:
            parent: Parent widget
            search_function: Function that takes a query string and returns search results
            placeholder: Placeholder text for the entry
            width: Width of the entry widget
            max_results: Maximum number of results to show
        """
        self.parent = parent
        self.search_function = search_function
        self.max_results = max_results
        self.search_thread = None
        self.last_search_time = 0
        self.debounce_delay = 0.5  # seconds
        
        # Create main frame
        self.frame = ttk.Frame(parent)
        
        # Create entry widget
        self.entry = ttk.Entry(self.frame, width=width)
        self.entry.pack(side=tk.LEFT, fill='x', expand=True)
        
        # Set placeholder
        self.entry.insert(0, placeholder)
        self.entry.bind('<FocusIn>', self.on_focus_in)
        self.entry.bind('<FocusOut>', self.on_focus_out)
        self.entry.bind('<KeyRelease>', self.on_key_release)
        
        # Create dropdown listbox
        self.dropdown = tk.Listbox(self.frame, height=0)
        self.dropdown.pack(side=tk.LEFT, fill='x', expand=True)
        self.dropdown.bind('<<ListboxSelect>>', self.on_select)
        
        # Initially hide dropdown
        self.dropdown.pack_forget()
        
        # Track if dropdown is visible
        self.is_dropdown_visible = False
        
    def on_focus_in(self, event):
        """Handle focus in event"""
        if self.entry.get() == "Search..." or self.entry.get() == "Search artists..." or \
           self.entry.get() == "Search songs..." or self.entry.get() == "Search genres..." or \
           self.entry.get() == "Search albums...":
            self.entry.delete(0, tk.END)
            self.entry.config(foreground='black')
    
    def on_focus_out(self, event):
        """Handle focus out event"""
        if not self.entry.get():
            self.entry.insert(0, "Search...")
            self.entry.config(foreground='gray')
        self.hide_dropdown()
    
    def on_key_release(self, event):
        """Handle key release event - trigger search"""
        query = self.entry.get().strip()
        
        # Don't search if query is too short or is placeholder
        if len(query) < 2 or query in ["Search...", "Search artists...", "Search songs...", "Search genres...", "Search albums..."]:
            self.hide_dropdown()
            return
        
        # Debounce search
        current_time = time.time()
        if current_time - self.last_search_time < self.debounce_delay:
            return
        
        self.last_search_time = current_time
        
        # Cancel previous search thread if running
        if self.search_thread and self.search_thread.is_alive():
            return
        
        # Start new search thread
        self.search_thread = threading.Thread(target=self.perform_search, args=(query,))
        self.search_thread.daemon = True
        self.search_thread.start()
    
    def perform_search(self, query: str):
        """Perform search in background thread"""
        try:
            results = self.search_function(query)
            
            # Update UI in main thread
            self.parent.after(0, lambda: self.update_dropdown(results))
        except Exception as e:
            print(f"Search error: {e}")
            # Update UI in main thread to show error
            self.parent.after(0, lambda: self.update_dropdown([]))
    
    def update_dropdown(self, results: List[Dict[str, Any]]):
        """Update dropdown with search results"""
        self.dropdown.delete(0, tk.END)
        
        if not results:
            self.hide_dropdown()
            return
        
        # Add results to dropdown
        for i, result in enumerate(results[:self.max_results]):
            display_text = self.format_result(result)
            self.dropdown.insert(tk.END, display_text)
        
        # Show dropdown
        self.show_dropdown()
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """Format a search result for display"""
        if 'name' in result and 'artist' in result:
            # Song result
            return f"{result['name']} - {result['artist']}"
        elif 'name' in result and 'release_date' in result:
            # Album result
            return f"{result['name']} - {result.get('artist', 'Unknown')} ({result['release_date']})"
        elif 'name' in result and 'popularity' in result:
            # Artist result
            return f"{result['name']} (Popularity: {result['popularity']})"
        elif isinstance(result, str):
            # Genre result
            return result
        else:
            # Fallback
            return str(result.get('name', 'Unknown'))
    
    def show_dropdown(self):
        """Show the dropdown"""
        if not self.is_dropdown_visible:
            self.dropdown.pack(side=tk.LEFT, fill='x', expand=True)
            self.is_dropdown_visible = True
    
    def hide_dropdown(self):
        """Hide the dropdown"""
        if self.is_dropdown_visible:
            self.dropdown.pack_forget()
            self.is_dropdown_visible = False
    
    def on_select(self, event):
        """Handle selection from dropdown"""
        selection = self.dropdown.curselection()
        if selection:
            selected_text = self.dropdown.get(selection[0])
            self.entry.delete(0, tk.END)
            self.entry.insert(0, selected_text)
            self.hide_dropdown()
    
    def get_value(self) -> str:
        """Get the current value from the entry"""
        value = self.entry.get().strip()
        # Don't return placeholder text
        if value in ["Search...", "Search artists...", "Search songs...", "Search genres...", "Search albums..."]:
            return ""
        return value
    
    def clear(self):
        """Clear the entry and hide dropdown"""
        self.entry.delete(0, tk.END)
        self.hide_dropdown()
    
    def set_value(self, value: str):
        """Set the entry value"""
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value) 