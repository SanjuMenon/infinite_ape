#!/usr/bin/env python3
"""
FSM Stacking Example

This example demonstrates advanced FSM stacking capabilities with a generic
scenario. It shows how to:

1. Start with a main FSM
2. Stack specialized sub-FSMs when needed
3. Handle context inheritance and return
4. Use different merge strategies for context handover
5. Preserve conversation history across FSM transitions

The scenario involves a main FSM that can delegate to specialized
sub-systems when specific functionality is required.
"""

from dotenv import load_dotenv
from llm_fsm import API
from llm_fsm.api import ContextMergeStrategy

load_dotenv()

def run_stacking_example():
    """
    Run the FSM builder example that helps users create their own FSM.
    """
    print("🤖 FSM Builder Bot: Let's create your FSM!")
    print("=" * 60)

    # Create the main FSM builder API from fsm.json
    api = API.from_file("fsm.json")

    print("\n📝 Starting FSM creation conversation...")

    # Start the main conversation
    try:
        conv_id, initial_response = api.start_conversation({
            "session_id": "fsm_builder_session_001",
            "timestamp": "2024-01-15T10:30:00Z"
        })

        print(f"🤖 FSM Builder: {initial_response}")
        print(f"📊 Stack depth: {api.get_stack_depth(conv_id)}")

        first_time = True
        metadata_collected = False

        while not api.has_conversation_ended(conv_id):
            # Get current state before processing
            current_state = api.get_current_state(conv_id)
            print(f"📍 Current state: {current_state}")

            # Get user input
            if first_time:
                user_input = "Lets Start Collecting Metadata First"
                first_time = False
            else:
                user_input = input("\n👤 You: ")
            
            # Process the message
            response = api.converse(user_input, conv_id)
            print(f"🤖 Response: {response}")

            # Check if we should delegate to metadata collector
            new_state = api.get_current_state(conv_id)
            if new_state == "delegate_to_metadata" and not metadata_collected:
                print("\n🔄 Delegating to Metadata Collector...")

                # Get current context
                current_context = api.get_data(conv_id)
                print(f"📋 Context to pass: {list(current_context.keys())}")

                # Push the metadata collector FSM onto the stack
                metadata_response = api.push_fsm(
                    conv_id,
                    "metafsm.json",
                    context_to_pass={
                        "fsm_name": current_context.get("fsm_name"),
                        "fsm_version": current_context.get("fsm_version"),
                        "fsm_persona": current_context.get("fsm_persona"),
                        "fsm_description": current_context.get("fsm_description"),
                    },
                    return_context={
                        "metadata_collection_completed": True,
                        "referral_source": "fsm_builder"
                    },
                    shared_context_keys=["fsm_name", "fsm_version", "fsm_persona", "fsm_description"],
                    preserve_history=True,
                    inherit_context=True
                )

                print(f"🤖 Metadata Collector: {metadata_response}")
                print(f"📊 Stack depth after push: {api.get_stack_depth(conv_id)}")

                # Handle metadata collection interaction
                while api.get_current_state(conv_id) != "metadata_complete":
                    metadata_input = input("\n👤 You: ")
                    metadata_resp = api.converse(metadata_input, conv_id)
                    print(f"🤖 Metadata Collector: {metadata_resp}")

                    # Check if we've reached the end of metadata collection
                    if api.get_current_state(conv_id) == "metadata_complete":
                        print("\n🔄 Metadata collection complete, returning to FSM builder...")

                        # Get the context from metadata collector before popping
                        metadata_context = api.get_data(conv_id)
                        print(f"📋 Collected metadata: {list(metadata_context.keys())}")

                        # Pop back to main FSM with collected metadata
                        return_response = api.pop_fsm(
                            conv_id,
                            context_to_return={
                                "metadata_collection_completed": True,
                                "fsm_name": metadata_context.get("fsm_name"),
                                "fsm_description": metadata_context.get("fsm_description"),
                                "fsm_version": metadata_context.get("fsm_version"),
                                "fsm_persona": metadata_context.get("fsm_persona")
                            },
                            merge_strategy=ContextMergeStrategy.UPDATE
                        )

                        print(f"🤖 Back to FSM Builder: {return_response}")
                        print(f"📊 Stack depth after pop: {api.get_stack_depth(conv_id)}")
                        metadata_collected = True
                        break

        # Display final results
        print("\n" + "=" * 60)
        print("📊 FSM CREATION SUMMARY")
        print("=" * 60)

        # Show final context
        final_context = api.get_data(conv_id)
        print(f"📋 Final Context Keys: {list(final_context.keys())}")

        # Show context flow
        context_flow = api.get_context_flow(conv_id)
        print(f"🔄 Context Flow: {context_flow}")

        # Show all stack data
        all_data = api.get_all_stack_data(conv_id)
        print(f"📚 Stack Data Levels: {len(all_data)}")

        print(f"\n✅ FSM creation completed successfully!")

    except Exception as e:
        print(f"❌ Error during FSM creation: {str(e)}")
        raise

    finally:
        # Clean up
        api.close()

if __name__ == "__main__":
    run_stacking_example()