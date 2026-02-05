"""Pipeline SDK client (front door)."""

from pathlib import Path
from typing import Optional

from instruction_sdk_compiler.compiler import compile_instruction, InstructionReceipt
from instruction_sdk_compiler.llm.base import LLMClient
from instruction_sdk_compiler.llm.openai_client import OpenAIClient
from instruction_sdk_compiler.parser.ir import ChangeSet
from instruction_sdk_compiler.patching.apply import apply_changeset, PatchRecord
from instruction_sdk_compiler.spec.model import SdkSpec
from instruction_sdk_compiler.codegen.renderer import render_sdk
from instruction_sdk_compiler.storage.persistence import save_spec, load_spec, replay_patches


class BuildResult:
    """Result of a build operation."""

    def __init__(self, output_dir: str, success: bool, message: str = ""):
        self.output_dir = output_dir
        self.success = success
        self.message = message


class CompilerClient:
    """Main client for the instruction SDK compiler."""

    def __init__(
        self,
        project_dir: str = "out_project",
        llm_client: Optional[LLMClient] = None,
    ):
        """
        Initialize compiler client.
        
        Args:
            project_dir: Directory for project output
            llm_client: LLM client (default: OpenAIClient)
        """
        self.project_dir = Path(project_dir)
        self.project_dir.mkdir(parents=True, exist_ok=True)
        
        self.llm_client = llm_client or OpenAIClient()
        
        # Initialize spec (try to load, otherwise start fresh)
        self._spec: SdkSpec
        self._patch_log: list[PatchRecord]
        self._spec, self._patch_log = load_spec(str(self.project_dir))
        
        # Ensure spec is initialized (dicts may be None)
        from instruction_sdk_compiler.patching.apply import _ensure_spec_initialized
        _ensure_spec_initialized(self._spec)

    def ingest_instruction(self, text: str) -> InstructionReceipt:
        """
        Ingest a natural language instruction.
        
        Args:
            text: Natural language instruction
            
        Returns:
            InstructionReceipt
        """
        # Compile instruction to changeset
        receipt = compile_instruction(text, self._spec, self.llm_client)
        
        # Apply changeset
        patch_record, self._spec = apply_changeset(self._spec, receipt.changeset, text)
        self._patch_log.append(patch_record)
        
        # Auto-save
        self.save()
        
        return receipt

    def ingest_changeset(
        self, changeset: ChangeSet, source_text: Optional[str] = None
    ) -> InstructionReceipt:
        """
        Ingest a ChangeSet directly (bypassing LLM).
        
        Args:
            changeset: Pre-validated ChangeSet
            source_text: Optional source instruction text
            
        Returns:
            InstructionReceipt
        """
        # Apply changeset
        patch_record, self._spec = apply_changeset(self._spec, changeset, source_text)
        self._patch_log.append(patch_record)
        
        # Auto-save
        self.save()
        
        return InstructionReceipt(
            instruction_text=source_text or "",
            changeset=changeset,
            validation_errors=None,
            repair_attempts=0,
        )

    def current_spec(self) -> SdkSpec:
        """
        Get the current SDK specification.
        
        Returns:
            Current SdkSpec
        """
        return self._spec

    def history(self) -> list[PatchRecord]:
        """
        Get the patch history.
        
        Returns:
            List of PatchRecord
        """
        return self._patch_log.copy()

    def build(self, output_dir: Optional[str] = None) -> BuildResult:
        """
        Build the generated SDK.
        
        Args:
            output_dir: Output directory (default: project_dir/generated_sdk)
            
        Returns:
            BuildResult
        """
        try:
            out_dir = output_dir or str(self.project_dir / "generated_sdk")
            render_sdk(self._spec, out_dir)
            return BuildResult(
                output_dir=out_dir,
                success=True,
                message=f"SDK generated successfully to {out_dir}",
            )
        except Exception as e:
            return BuildResult(
                output_dir=output_dir or str(self.project_dir / "generated_sdk"),
                success=False,
                message=f"Build failed: {str(e)}",
            )

    def save(self) -> None:
        """Save spec and patch log to disk."""
        save_spec(self._spec, self._patch_log, str(self.project_dir))

    def load(self) -> None:
        """Load spec and patch log from disk."""
        self._spec, self._patch_log = load_spec(str(self.project_dir))

    def rollback(self, n: int) -> None:
        """
        Rollback the last n patches.
        
        Args:
            n: Number of patches to rollback
        """
        if n < 0:
            raise ValueError("n must be non-negative")
        if n > len(self._patch_log):
            raise ValueError(f"Cannot rollback {n} patches (only {len(self._patch_log)} exist)")
        
        # Rebuild spec from initial empty spec + patches up to len-n
        initial_spec = SdkSpec(version="1.0.0")
        # Initialize empty dicts - apply_changeset will handle initialization
        target_index = len(self._patch_log) - n
        self._spec = replay_patches(initial_spec, self._patch_log, up_to=target_index)
        
        # Truncate patch log
        self._patch_log = self._patch_log[:target_index]
        
        # Save
        self.save()
