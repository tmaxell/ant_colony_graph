import tkinter as tk
from tkinter import ttk
import networkx as nx
import math
from itertools import permutations
import random

class AntColony:
    def __init__(self, graph, ants_count=10, evaporation_rate=0.1, pheromone_deposit=1, alpha=1, beta=2, iterations=100):
        self.graph = graph
        self.ants_count = ants_count
        self.evaporation_rate = evaporation_rate
        self.pheromone_deposit = pheromone_deposit
        self.alpha = alpha
        self.beta = beta
        self.iterations = iterations

    def find_shortest_path(self):
        shortest_path = None
        min_cycle_length = float('inf')

        for _ in range(self.iterations):
            paths = self.generate_ant_paths()
            self.update_pheromones(paths)
            current_shortest_path, current_cycle_length = self.get_shortest_path(paths)
            if current_cycle_length < min_cycle_length:
                shortest_path = current_shortest_path
                min_cycle_length = current_cycle_length

        return shortest_path, min_cycle_length

    def generate_ant_paths(self):
        paths = []
        for _ in range(self.ants_count):
            path = self.generate_ant_path()
            paths.append(path)
        return paths

    def generate_ant_path(self):
        nodes = list(self.graph.nodes)
        random.shuffle(nodes)
        return nodes

    def update_pheromones(self, paths):
        for path in paths:
            cycle_length = sum(self.graph[path[i]][path[i+1]]['weight'] for i in range(len(path) - 1))
            cycle_length += self.graph[path[-1]][path[0]]['weight']
            for i in range(len(path) - 1):
                self.graph[path[i]][path[i+1]]['pheromone'] += self.pheromone_deposit / cycle_length
            self.graph[path[-1]][path[0]]['pheromone'] += self.pheromone_deposit / cycle_length

        for edge in self.graph.edges:
            self.graph.edges[edge]['pheromone'] *= (1 - self.evaporation_rate)

    def get_shortest_path(self, paths):
        min_cycle_length = float('inf')
        shortest_path = None
        for path in paths:
            cycle_length = sum(self.graph[path[i]][path[i+1]]['weight'] for i in range(len(path) - 1))
            cycle_length += self.graph[path[-1]][path[0]]['weight']
            if cycle_length < min_cycle_length:
                min_cycle_length = cycle_length
                shortest_path = path
        return shortest_path, min_cycle_length


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

        min_cycle_length = float('inf')
        min_hamiltonian_cycle = None

        for start_node in self.nodes:
            current_node = start_node
            cycle = [current_node]
            remaining_nodes = set(self.nodes)
            remaining_nodes.remove(start_node)

            while remaining_nodes:
                closest_node = min(remaining_nodes, key=lambda node: self.distance(current_node, node))
                cycle.append(closest_node)
                remaining_nodes.remove(closest_node)
                current_node = closest_node

            cycle_length = sum(self.distance(cycle[i], cycle[i+1]) for i in range(len(cycle) - 1))
            cycle_length += self.distance(cycle[-1], cycle[0])

            if cycle_length < min_cycle_length:
                min_cycle_length = cycle_length
                min_hamiltonian_cycle = cycle

        print("Кратчайший гамильтонов цикл:", min_hamiltonian_cycle)
        print("Стоимость всего пути:", min_cycle_length)

        self.canvas.delete("cycle")
        for i in range(len(min_hamiltonian_cycle) - 1):
            x1, y1 = map(int, min_hamiltonian_cycle[i].strip("()").split(", "))
            x2, y2 = map(int, min_hamiltonian_cycle[i+1].strip("()").split(", "))
            self.canvas.create_line(x1, y1, x2, y2, fill="red", arrow=tk.LAST, tags="cycle")
        x1, y1 = map(int, min_hamiltonian_cycle[-1].strip("()").split(", "))
        x2, y2 = map(int, min_hamiltonian_cycle[0].strip("()").split(", "))
        self.canvas.create_line(x1, y1, x2, y2, fill="red", arrow=tk.LAST, tags="cycle")

        self.table.insert("", "end", values=("Итоговая стоимость пути:", "", f"{min_cycle_length:.2f}"))



    def clear_canvas(self):
        self.graph.clear()
        self.nodes.clear()
        self.edges.clear()
        self.canvas.delete("all")
        self.table.delete(*self.table.get_children())
        self.node_count = 1

    def distance(self, node1, node2):
        x1, y1 = map(int, node1.strip("()").split(", "))
        x2, y2 = map(int, node2.strip("()").split(", "))
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


if __name__ == "__main__":
    root = tk.Tk()
    app = GraphApp(root)
    root.mainloop()
