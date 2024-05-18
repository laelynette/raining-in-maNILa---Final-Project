import numpy as np
from mealpy import PermutationVar, Problem
from haversine import haversine, Unit
import math

class RouteFinder(Problem):
    def __init__(self, bounds=None, minmax="min", data=None):
        self.data = data
        self.eps = 1e10  # Penalty function for vertex with 0 connection
        super().__init__(bounds, minmax)

    # Calculate the fitness of an individual
    def obj_func(self, x):
        x_decoded = self.decode_solution(x)
        individual = x_decoded["path"]

        total_distance = 0
        for idx in range(len(individual) - 1):
            start_node = individual[idx]
            end_node = individual[idx + 1]
            weight = self.data[start_node, end_node]
            if weight == 0:
                return self.eps
            total_distance += weight
        return total_distance

class Meta(RouteFinder):
    def __init__(self, waypoint, orig, dest, model_params):
        self.waypoint = waypoint
        self.graph = {}
        self.orig = orig
        self.dest = dest
        self.model = model_params['model']
        self.epoch = model_params['epoch']
        self.pop_size = model_params['pop_size']
        #self.dropout = (random.randrange(20, 80))/100
        self.dropout = 0.60 

        self.path = [0, 0]
        self.orig_to_dest = [0, 0]
        self.graph_mat = []
        self.num_vertices = len(self.graph_mat)
        self.check_dist = 0

        self.coordsOrig = waypoint[orig]
        self.coordsDest = waypoint[dest]

        self.check_dist = haversine(self.coordsOrig, self.coordsDest, unit=Unit.KILOMETERS)

        '''
        model_params = {model, epoch, population size}

        model - has to be a mealpy class (eg. ACOR, WOA, GA...)
        epoch - must be int type only
        population size - must also be int type
        '''

    ## Creates model
    def __create_model(self, graph):
        num_nodes = len(graph)
        bounds = PermutationVar(valid_set=list(range(0, num_nodes)), name="path")
        problem = RouteFinder(bounds=bounds, minmax="min", data=graph)
        model = self.model(self.epoch, self.pop_size)
        model.solve(problem)

        return model

    ## Validates traversal order 
    def __validate_order(self, model):
        check_model_dist = model.problem.decode_solution(model.g_best.solution)['path']
        return check_model_dist.index(self.orig_to_dest[0]) > check_model_dist.index(self.orig_to_dest[1])

    def __update_graph(self, new_graph):
        self.graph = new_graph

    def __update_graph_mat(self, new_mat):
        self.graph_mat = new_mat

    ## Generates graph from coordinates
    def __generate_graph(self, waypoint):
        graph = {}

        for city1, coords1 in waypoint.items():
            graph[city1] = {}
            for city2, coords2 in waypoint.items():
                if city1 != city2:
                    distance = haversine(coords1, coords2, unit=Unit.KILOMETERS)
                    graph[city1][city2] = round(distance, 2)

        self.graph = graph

    def __remove_edge(self, node1, node2):
        if node1 in self.graph and node2 in self.graph[node1]:
            del self.graph[node1][node2]
        if node2 in self.graph and node1 in self.graph[node2]:
            del self.graph[node2][node1]

    ## Creates a matrix from graph
    def __create_graph_matrix(self, graph):
        nodes = sorted(graph.keys())
        nodes = sorted(list(graph.keys()))
        num_nodes = len(nodes)
        graph_matrix = np.zeros((num_nodes, num_nodes))

        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes):
                if node2 in graph[node1]:
                    graph_matrix[i][j] = graph[node1][node2]

        return graph_matrix

    ## Maps the index to the graph, traversing through the node
    def __map_result_to_graph(self, result):
        mapped_result = []
        for node_index in result:
            node_name = list(sorted(self.graph.keys()))[node_index]
            mapped_result.append(node_name)
        return mapped_result # returns list of char

    ## Calculates the distance from start node to end node
    def __calculate_distance(self, graph, nodes):
        total_distance = 0
        for i in range(len(nodes) - 1):
            current_node = nodes[i]
            next_node = nodes[i + 1]
            if current_node in graph and next_node in graph[current_node]:
                total_distance += graph[current_node][next_node]
            else:
                print(f"No direct connection between {current_node} and {next_node}.")
                total_distance += np.inf  # In case no edge, add infinity to represent no connection
        return total_distance # returns float

    ## Creates a new graph from the previous graph
    def __create_subgraph(self, graph, nodes_to_go_through):
        subgraph = {}
        for node in nodes_to_go_through:
            if node in graph:
                subgraph[node] = {}
                for neighbor, distance in graph[node].items():
                    if neighbor in nodes_to_go_through:
                        subgraph[node][neighbor] = distance

        # Remove edges between the first and last nodes
        if nodes_to_go_through[0] in subgraph and nodes_to_go_through[-1] in subgraph[nodes_to_go_through[0]]:
            del subgraph[nodes_to_go_through[0]][nodes_to_go_through[-1]]
        if nodes_to_go_through[-1] in subgraph and nodes_to_go_through[0] in subgraph[nodes_to_go_through[-1]]:
            del subgraph[nodes_to_go_through[-1]][nodes_to_go_through[0]]

        return subgraph

    ## Updates nodes
    def __update_start_end(self, new_start, new_end):
        self.orig_to_dest[0] = (new_start)
        self.orig_to_dest[1] = (new_end)

    ## Update params of the model
    def __update_params(self):
        if self.epoch > 5 and self.pop_size > 5:
            self.epoch = self.epoch - math.ceil(self.epoch*self.dropout)
        else:
          pass

    ## Update node idx
    def __update_node_idx(self):
        nodes = sorted(self.graph.keys())
        node_idx = {node: i for i, node in enumerate(nodes)}

        self.path[0] = node_idx[self.orig]
        self.path[1] = node_idx[self.dest]

    ## Runs the code
    def run_meta(self):

        ## Initialize starting parameters
        self.__generate_graph(self.waypoint) ## Generate graph
        self.__remove_edge(self.orig, self.dest)

        mat = self.__create_graph_matrix(self.graph)
        self.__update_graph_mat(mat) # Updates graph into matrix
        self.__update_node_idx()
        self.__update_start_end(self.path[0], self.path[1])

        for _ in range(100):
            while True:
                model = self.__create_model(self.graph_mat)
                if not self.__validate_order(model):
                    break

            path = model.problem.decode_solution(model.g_best.solution)['path']
            path = path[path.index(self.orig_to_dest[0]):path.index(self.orig_to_dest[1])+1] # Takes the orig to dest route


            map_result = self.__map_result_to_graph(path)
            distance = self.__calculate_distance(self.graph, map_result) # Gets distance 

            sub_graph = self.__create_subgraph(self.graph, map_result) # New graph created
            self.__update_graph(sub_graph)

            self.__update_node_idx()

            self.__update_start_end(self.path[0], self.path[1]) # update origin and dest
            self.__update_graph_mat(self.__create_graph_matrix(self.graph))
            self.__update_params()

            if distance <= self.check_dist:
              break

        return map_result, np.round(distance,2), np.round(self.check_dist, 2)