from rich.tree import Tree
from rich import print

second_tree = Tree("second Tree")
second_tree.add("test")
tree = Tree("Rich Tree")
baz_tree = tree.add(second_tree)

print(tree)
