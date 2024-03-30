import tkinter as tk
from tkinter import ttk
import networkx as nx
import math
import random

class GraphApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Поиск кратчайшего гамильтонова цикла")

        self.graph = nx.Graph()
        self.nodes = []
        self.edges = []
        self.start_node = None

        self.canvas = tk.Canvas(self.root, width=600, height=400)
        self.canvas.pack()

        self.canvas.bind("<Button-1>", self.add_node)
        self.canvas.bind("<Button-2>", self.start_edge)

        self.frame = ttk.Frame(self.root)
        self.frame.pack()

        self.find_cycle_button = ttk.Button(self.frame, text="Поиск цикла", command=self.find_cycle)
        self.find_cycle_button.grid(row=0, column=0)

        self.clear_button = ttk.Button(self.frame, text="Очистить полотно", command=self.clear_canvas)
        self.clear_button.grid(row=0, column=1)

        self.table = ttk.Treeview(self.frame, columns=("start", "end", "weight"), show="headings")
        self.table.heading("start", text="Начальная вершина")
        self.table.heading("end", text="Конечная вершина")
        self.table.heading("weight", text="Вес ребра")
        self.table.grid(row=1, column=0, columnspan=2)

        self.node_count = 1

    def add_node(self, event):
        x, y = event.x, event.y
        node = f"({x}, {y})"
        if node not in self.nodes:
            self.graph.add_node(node)
            self.nodes.append(node)
            self.table.insert("", "end", values=(node, "", ""))
            self.canvas.create_oval(x-5, y-5, x+5, y+5, fill="black")
            self.canvas.create_text(x, y, text=str(self.node_count), fill="white")
            self.node_count += 1

    def start_edge(self, event):
        x, y = event.x, event.y
        closest_node = None
        min_distance = float('inf')
        for node in self.nodes:
            nx, ny = map(int, node.strip("()").split(", "))
            distance = ((x - nx) ** 2 + (y - ny) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                closest_node = node
        if closest_node:
            if self.start_node is None:
                self.start_node = closest_node
            else:
                end_node = closest_node
                weight = min_distance
                if (self.start_node, end_node) not in self.edges and (end_node, self.start_node) not in self.edges:
                    self.graph.add_edge(self.start_node, end_node, weight=weight)
                    self.edges.append((self.start_node, end_node, weight))
                    self.table.insert("", "end", values=(self.start_node, end_node, f"{weight:.2f}"))
                    x1, y1 = map(int, self.start_node.strip("()").split(", "))
                    x2, y2 = map(int, end_node.strip("()").split(", "))
                    self.canvas.create_line(x1, y1, x2, y2, fill="blue")
                self.start_node = None

    def find_cycle(self):
        if len(self.nodes) < 3:
            print("Недостаточно вершин для построения цикла")
            return

        ant_count = 10
        generations = 100
        evaporation_rate = 0.5
        pheromone_constant = 100
        visibility_constant = 100

        def initial_pheromone():
            return {edge: 1 for edge in self.graph.edges()}

        def calculate_visibility():
            return {edge: 1 / weight for edge, weight in nx.get_edge_attributes(self.graph, 'weight').items()}

        def update_pheromone(trails, ants):
            for edge in trails.keys():
                pheromone = trails[edge]
                for ant in ants:
                    if edge in ant.trail:
                        pheromone += pheromone_constant / ant.trail_length()
                pheromone *= evaporation_rate
                trails[edge] = max(pheromone, 0.1)  # Ensure pheromone doesn't become zero

        def select_next_node(current_node, available_nodes, pheromone, visibility):
            probabilities = []
            total_prob = 0
            for node in available_nodes:
                edge = (current_node, node)
                probabilities.append((node, (pheromone[edge] ** alpha) * (visibility[edge] ** beta)))
                total_prob += probabilities[-1][1]
            probabilities = [(node, prob / total_prob) for node, prob in probabilities]
            selected_node = None
            r = random.uniform(0, 1)
            for node, prob in probabilities:
                if r <= prob:
                    selected_node = node
                    break
                else:
                    r -= prob
            if selected_node is None:
                selected_node = random.choice(available_nodes)
            return selected_node

        trails = initial_pheromone()
        visibility = calculate_visibility()
        best_path = None
        best_length = float('inf')

        for _ in range(generations):
            ants = [Ant(self.graph.nodes(), select_next_node) for _ in range(ant_count)]
            for ant in ants:
                ant.move(trails, visibility)
                if ant.trail_length() < best_length:
                    best_path = ant.trail
                    best_length = ant.trail_length()
            update_pheromone(trails, ants)

        print("Кратчайший гамильтонов цикл:", best_path)
        print("Стоимость всего пути:", best_length)

        self.canvas.delete("cycle")
        for i in range(len(best_path) - 1):
            x1, y1 = map(int, best_path[i].strip("()").split(", "))
            x2, y2 = map(int, best_path[i+1].strip("()").split(", "))
            self.canvas.create_line(x1, y1, x2, y2, fill="red", arrow=tk.LAST, tags="cycle")
        x1, y1 = map(int, best_path[-1].strip("()").split(", "))
        x2, y2 = map(int, best_path[0].strip("()").split(", "))
        self.canvas.create_line(x1, y1, x2, y2, fill="red", arrow=tk.LAST, tags="cycle")

        self.table.insert("", "end", values=("Итоговая стоимость пути:", "", f"{best_length:.2f}"))

    def clear_canvas(self):
        self.graph.clear()
        self.nodes.clear()
        self.edges.clear()
        self.canvas.delete("all")
        self.table.delete(*self.table.get_children())
        self.node_count = 1

class Ant:
    def __init__(self, nodes, select_next_node):
        self.nodes = nodes
        self.select_next_node = select_next_node
        self.trail = []
        self.visited = set()

    def move(self, trails, visibility):
        if not self.trail:
            self.trail.append(random.choice(list(self.nodes)))
        while len(self.trail) < len(self.nodes):
            current_node = self.trail[-1]
            available_nodes = list(self.nodes - self.visited)
            next_node = self.select_next_node(current_node, available_nodes, trails, visibility)
            self.trail.append(next_node)
            self.visited.add(next_node)

    def trail_length(self):
        length = 0
        for i in range(len(self.trail) - 1):
            edge = (self.trail[i], self.trail[i+1])
            length += self.distance(edge[0], edge[1])
        length += self.distance(self.trail[-1], self.trail[0])
        return length

    def distance(self, node1, node2):
        x1, y1 = map(int, node1.strip("()").split(", "))
        x2, y2 = map(int, node2.strip("()").split(", "))
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

if __name__ == "__main__":
    root = tk.Tk()
    app = GraphApp(root)
    root.mainloop()
