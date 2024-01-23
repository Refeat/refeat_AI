import sys
import time
from typing import Any, List, Dict, Optional

from langchain_core.outputs import LLMResult
from langchain.callbacks.streaming_stdout_final_only import FinalStreamingStdOutCallbackHandler

class CustomStreamingStdOutCallbackHandler(FinalStreamingStdOutCallbackHandler):
    """Callback handler for streaming in agents.
    Only works with agents using LLMs that support streaming.

    The output will be streamed until "<END" is reached.
    """
    def __init__(
        self,
        *,
        answer_prefix_tokens: Optional[List[str]] = ['final', ' answer', '":'],
        strip_tokens: bool = True,
        stream_prefix: bool = False,
        special_tokens: Optional[List[str]] = ['}',  ' "', '"'],
        queue,
    ) -> None:
        """Instantiate EofStreamingStdOutCallbackHandler.

        Args:
            answer_prefix_tokens: Token sequence that prefixes the anwer.
                Default is ['final', ' answer', '":']
            end_of_file_token: Token that signals end of file.
                Default is "END"
            strip_tokens: Ignore white spaces and new lines when comparing
                answer_prefix_tokens to last tokens? (to determine if answer has been
                reached)
            stream_prefix: Should answer prefix itself also be streamed?
        """
        super().__init__(
            answer_prefix_tokens=answer_prefix_tokens,
            strip_tokens=strip_tokens,
            stream_prefix=stream_prefix,
        )
        self.queue = queue
        self.special_tokens = special_tokens

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""
        # Remember the last n tokens, where n = len(answer_prefix_tokens)
        self.append_to_last_tokens(token)
        # Check if the last n tokens match the answer_prefix_tokens list ...
        if self.check_if_answer_reached():
            self.answer_reached = True
            if self.stream_prefix:
                for t in self.last_tokens:
                    sys.stdout.write(t)
                sys.stdout.flush()
            return

        # ... if yes, then print tokens from now on
        if self.answer_reached:
            if token not in self.special_tokens:
                sys.stdout.write(token)
                sys.stdout.flush()
                self.queue.append(token)

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Run when LLM ends running."""
        self.queue.append('END')

    def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        """Run when LLM errors."""
        print('ERROR')
        print(self.queue)
        self.queue.append('ERROR')
        
    def on_chain_error(self, error: BaseException, **kwargs: Any) -> None:
        """Run when chain errors."""
        print('ERROR')
        print(self.queue)
        self.queue.append('ERROR')