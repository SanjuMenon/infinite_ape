import argparse
import json
import sys

from dotenv import load_dotenv

from . import fetch_nodes_by_parent, fetch_node_by_id, fetch_all_descendants, fetch_subtree


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Workflowy API demo: fetch nodes by parent or by id.")
	group = parser.add_mutually_exclusive_group()
	group.add_argument("--parent-id", type=str, default="inbox", help="Parent id or target key (e.g., 'inbox'). Default: inbox")
	group.add_argument("--node-id", type=str, help="Specific node UUID to retrieve.")
	parser.add_argument("--recursive", action="store_true", help="If set with --parent-id or --node-id, fetch entire subtree (nested).")
	parser.add_argument("--max-depth", type=int, default=None, help="Limit depth for recursive traversal (None = unlimited).")
	parser.add_argument("--indent", type=int, default=2, help="JSON pretty-print indent. Default: 2")
	return parser.parse_args()


def main() -> int:
	load_dotenv(override=False)
	args = parse_args()
	try:
		if args.recursive:
			# Prefer subtree from a specific node if provided, else from parent target/id
			root_id = args.node_id or args.parent_id
			result = fetch_subtree(root_id, max_depth=args.max_depth)
		elif args.node_id:
			result = fetch_node_by_id(args.node_id)
		else:
			result = fetch_nodes_by_parent(args.parent_id)
		print(json.dumps(result, indent=args.indent))
		return 0
	except Exception as exc:
		print(f"Error: {exc}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	raise SystemExit(main())

