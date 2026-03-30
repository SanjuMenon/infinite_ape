"""
Lightweight Workflowy API client to retrieve nodes.

Environment:
- Set WORKFLOWY_API_KEY in your .env (root of repo).

Example:
    from tarpit_model.workflowy import fetch_nodes_by_parent, fetch_node_by_id

    inbox_nodes = fetch_nodes_by_parent("inbox")
    a_node = fetch_node_by_id("your-node-id")
"""
import os
from typing import Any, Dict, Optional, List

import requests
from dotenv import load_dotenv


class WorkflowyClient:
	def __init__(self, api_key: Optional[str] = None, base_url: str = "https://workflowy.com/api/v1"):
		load_dotenv(override=False)
		self.api_key = api_key or os.getenv("WORKFLOWY_API_KEY") or os.getenv("WORKFLOWY_TOKEN") or os.getenv("WORKFLOWY_API_TOKEN")
		if not self.api_key:
			raise RuntimeError("Workflowy API key not found. Set WORKFLOWY_API_KEY in your .env")
		self.base_url = base_url.rstrip("/")

	def _headers(self) -> Dict[str, str]:
		return {
			"Authorization": f"Bearer {self.api_key}",
			"Accept": "application/json",
		}

	def fetch_nodes(self, parent_id: Optional[str] = None, node_id: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
		if parent_id and node_id:
			raise ValueError("Provide only one of parent_id or node_id.")

		# Retrieve a single node
		if node_id:
			url = f"{self.base_url}/nodes/{node_id}"
			response = requests.get(url, headers=self._headers(), timeout=30)
		else:
			# List child nodes under a parent
			query: Dict[str, Any] = {}
			if parent_id:
				query["parent_id"] = parent_id
			if params:
				query.update(params)
			url = f"{self.base_url}/nodes"
			response = requests.get(url, headers=self._headers(), params=query, timeout=30)

		if response.status_code == 401:
			raise PermissionError("Unauthorized. Check your Workflowy API key.")
		if response.status_code == 404:
			raise LookupError("Requested node not found.")
		response.raise_for_status()
		return response.json()


def fetch_nodes_by_parent(parent_id: str = "inbox") -> Dict[str, Any]:
	client = WorkflowyClient()
	return client.fetch_nodes(parent_id=parent_id)


def fetch_node_by_id(node_id: str) -> Dict[str, Any]:
	client = WorkflowyClient()
	return client.fetch_nodes(node_id=node_id)


def fetch_children(parent_id: str) -> List[Dict[str, Any]]:
	"""
	Return the list of immediate child nodes under the given parent.
	"""
	client = WorkflowyClient()
	result = client.fetch_nodes(parent_id=parent_id)
	return result.get("nodes", [])


def fetch_child_ids(parent_id: str) -> List[str]:
	"""
	Return only the IDs of the immediate children under the given parent.
	"""
	children = fetch_children(parent_id)
	return [child.get("id") for child in children if isinstance(child, dict) and "id" in child]


def fetch_all_descendants(parent_id: str, max_depth: Optional[int] = None) -> List[Dict[str, Any]]:
	"""
	Breadth-first traversal to fetch all descendant nodes under the given parent.
	Returns a flat list of node dicts. Set max_depth to limit how deep to traverse
	(1 means only direct children, 2 includes grandchildren, etc.). None means no limit.
	"""
	results: List[Dict[str, Any]] = []
	queue: List[Dict[str, Any]] = [{"id": parent_id, "depth": 0}]

	while queue:
		current = queue.pop(0)
		current_depth = current["depth"]
		if max_depth is not None and current_depth >= max_depth:
			continue

		children = fetch_children(current["id"])
		results.extend(children)
		for child in children:
			child_id = child.get("id")
			if child_id:
				queue.append({"id": child_id, "depth": current_depth + 1})

	return results


def fetch_subtree(node_id: str, max_depth: Optional[int] = None) -> Dict[str, Any]:
	"""
	Build and return a nested subtree rooted at node_id.
	The returned dict has the root node fields and a 'children' list of subtrees.
	"""
	root_resp = fetch_node_by_id(node_id)
	root = root_resp.get("node", {}) if isinstance(root_resp, dict) else {}

	def build(current_id: str, depth: int) -> List[Dict[str, Any]]:
		if max_depth is not None and depth >= max_depth:
			return []
		children = fetch_children(current_id)
		nested_children: List[Dict[str, Any]] = []
		for child in children:
			child_id = child.get("id")
			if not child_id:
				continue
			# Copy to avoid mutating original dicts
			child_with_kids = dict(child)
			child_with_kids["children"] = build(child_id, depth + 1)
			nested_children.append(child_with_kids)
		return nested_children

	root["children"] = build(node_id, 0)
	return root

