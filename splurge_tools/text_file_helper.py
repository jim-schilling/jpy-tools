"""
Text file utility functions for common file operations.

This module provides helper methods for working with text files, including
line counting, file previewing, and file loading capabilities. The TextFileHelper
class implements static methods for efficient file operations without requiring
class instantiation.

Key features:
- Line counting for text files
- File previewing with configurable line limits
- Complete file loading with header/footer skipping
- Streaming file loading with configurable chunk sizes
- Configurable whitespace handling and encoding

Copyright (c) 2025 Jim Schilling

Please preserve this header and all related material when sharing!

This software is licensed under the MIT License.
"""

from collections import deque
from os import PathLike
from typing import List, Union, Iterator


class TextFileHelper:
    """
    Utility class for text file operations.
    All methods are static and memory efficient.
    """

    @staticmethod
    def line_count(
        file_name: Union[PathLike, str],
        *,
        encoding: str = "utf-8"
    ) -> int:
        """
        Count the number of lines in a text file.

        This method efficiently counts lines by iterating through the file
        without loading it entirely into memory.

        Args:
            file_name: Path to the text file
            encoding: File encoding to use (default: 'utf-8')

        Returns:
            int: Number of lines in the file

        Raises:
            FileNotFoundError: If the specified file doesn't exist
            IOError: If there are issues reading the file
            UnicodeDecodeError: If the file cannot be decoded with the specified encoding
        """
        with open(file_name, "r", encoding=encoding) as stream:
            return sum(1 for _ in stream)

    @staticmethod
    def preview(
        file_name: Union[PathLike, str],
        *,
        max_lines: int = 100,
        strip: bool = True,
        encoding: str = "utf-8",
        skip_header_rows: int = 0
    ) -> List[str]:
        """
        Preview the first N lines of a text file.

        This method reads up to max_lines from the beginning of the file,
        optionally stripping whitespace from each line and skipping header rows.

        Args:
            file_name: Path to the text file
            max_lines: Maximum number of lines to read (default: 100)
            strip: Whether to strip whitespace from lines (default: True)
            encoding: File encoding to use (default: 'utf-8')
            skip_header_rows: Number of rows to skip from the start (default: 0)

        Returns:
            List[str]: List of lines from the file

        Raises:
            ValueError: If max_lines < 1
            FileNotFoundError: If the specified file doesn't exist
            IOError: If there are issues reading the file
            UnicodeDecodeError: If the file cannot be decoded with the specified encoding
        """
        if max_lines < 1:
            raise ValueError("TextFileHelper.preview: max_lines is less than 1")
        
        skip_header_rows = max(0, skip_header_rows)
        lines: List[str] = []
        
        with open(file_name, "r", encoding=encoding) as stream:
            # Skip header rows
            for _ in range(skip_header_rows):
                if not stream.readline():
                    return lines
            
            # Read up to max_lines after skipping headers
            for _ in range(max_lines):
                line = stream.readline()
                if not line:
                    break
                lines.append(line.strip() if strip else line.rstrip("\n"))
        
        return lines

    @staticmethod
    def load_as_stream(
        file_name: Union[PathLike, str],
        *,
        strip: bool = True,
        encoding: str = "utf-8",
        skip_header_rows: int = 0,
        skip_footer_rows: int = 0,
        chunk_size: int = 500
    ) -> Iterator[List[str]]:
        """
        Load a text file as a stream of line chunks.

        This method yields chunks of lines from the file, allowing for
        memory-efficient processing of large files. Each chunk contains
        up to chunk_size lines. Uses a sliding window approach to handle
        footer row skipping without loading the entire file into memory.

        Args:
            file_name: Path to the text file
            strip: Whether to strip whitespace from lines (default: True)
            encoding: File encoding to use (default: 'utf-8')
            skip_header_rows: Number of rows to skip from the start (default: 0)
            skip_footer_rows: Number of rows to skip from the end (default: 0)
            chunk_size: Number of lines per chunk (default: 500)

        Yields:
            List[str]: Chunks of lines from the file

        Raises:
            ValueError: If chunk_size < 100
            FileNotFoundError: If the specified file doesn't exist
            IOError: If there are issues reading the file
            UnicodeDecodeError: If the file cannot be decoded with the specified encoding
        """
        if chunk_size < 100:
            raise ValueError("TextFileHelper.load_as_stream: chunk_size is less than 100")
        
        skip_header_rows = max(0, skip_header_rows)
        skip_footer_rows = max(0, skip_footer_rows)
        
        with open(file_name, "r", encoding=encoding) as stream:
            # Skip header rows
            for _ in range(skip_header_rows):
                if not stream.readline():
                    return
            
            # Use a sliding window to handle footer skipping efficiently
            if skip_footer_rows > 0:
                # Buffer to hold the last skip_footer_rows lines
                buffer: deque[str] = deque(maxlen=skip_footer_rows)
                current_chunk: List[str] = []
                
                for line in stream:
                    processed_line = line.strip() if strip else line.rstrip("\n")
                    
                    # Add to buffer for potential footer skipping
                    buffer.append(processed_line)
                    
                    # If buffer is full, move oldest line to current chunk
                    if len(buffer) == skip_footer_rows:
                        current_chunk.append(buffer.popleft())
                        
                        # Yield chunk when it reaches the desired size
                        if len(current_chunk) >= chunk_size:
                            yield current_chunk
                            current_chunk = []
                
                # Handle remaining lines (excluding the last skip_footer_rows)
                # The buffer now contains exactly the footer rows to skip
                # All other lines have already been processed and yielded
                
                # Yield any remaining lines in the final chunk
                if current_chunk:
                    yield current_chunk
            else:
                # No footer skipping needed - simple streaming
                current_chunk: List[str] = []
                
                for line in stream:
                    processed_line = line.strip() if strip else line.rstrip("\n")
                    current_chunk.append(processed_line)
                    
                    # Yield chunk when it reaches the desired size
                    if len(current_chunk) >= chunk_size:
                        yield current_chunk
                        current_chunk = []
                
                # Yield any remaining lines in the final chunk
                if current_chunk:
                    yield current_chunk

    @staticmethod
    def load(
        file_name: Union[PathLike, str],
        *,
        strip: bool = True,
        encoding: str = "utf-8",
        skip_header_rows: int = 0,
        skip_footer_rows: int = 0
    ) -> List[str]:
        """
        Load the entire contents of a text file into a list of strings.

        This method reads the complete file into memory, with options to
        strip whitespace from each line and skip header/footer rows.

        Args:
            file_name: Path to the text file
            strip: Whether to strip whitespace from lines (default: True)
            encoding: File encoding to use (default: 'utf-8')
            skip_header_rows: Number of rows to skip from the start (default: 0)
            skip_footer_rows: Number of rows to skip from the end (default: 0)

        Returns:
            List[str]: List of all lines from the file, excluding skipped rows

        Raises:
            FileNotFoundError: If the specified file doesn't exist
            IOError: If there are issues reading the file
            UnicodeDecodeError: If the file cannot be decoded with the specified encoding
        """
        skip_header_rows = max(0, skip_header_rows)
        skip_footer_rows = max(0, skip_footer_rows)
        with open(file_name, "r", encoding=encoding) as stream:
            for _ in range(skip_header_rows):
                if not stream.readline():
                    return []
            lines: List[str] = [line.strip() if strip else line.rstrip("\n") for line in stream]
            if skip_footer_rows > 0:
                if skip_footer_rows >= len(lines):
                    return []
                lines = lines[:-skip_footer_rows]
            return lines
