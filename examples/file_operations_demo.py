import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from tools.file_operations import FileOperationsTool
import time

console = Console()

def display_menu():
    """Display the main menu."""
    console.print(Panel.fit(
        "[bold blue]File Operations Demo[/bold blue]\n\n"
        "1. List Directory Contents\n"
        "2. Read File\n"
        "3. Write File\n"
        "4. Delete File\n"
        "5. Copy File\n"
        "6. Move File\n"
        "7. Search Files\n"
        "8. Compress File\n"
        "9. Search Content\n"
        "10. Compare Files\n"
        "11. Compare Binary Files\n"
        "12. Merge Files\n"
        "13. Advanced Content Search\n"
        "14. Synchronize Directories\n"
        "15. Monitor Directory\n"
        "16. Create Backup\n"
        "17. Encrypt File\n"
        "18. Decrypt File\n"
        "19. Verify File Integrity\n"
        "20. Create Archive\n"
        "21. Extract Archive\n"
        "22. Exit",
        title="Menu"
    ))

def display_directory_contents(result):
    """Display directory contents in a table."""
    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return

    table = Table(title=f"Contents of {result['path']}")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Size", style="yellow")
    table.add_column("Modified", style="magenta")

    for item in result["contents"]:
        size = f"{item['size']:,} bytes" if item["size"] else "-"
        table.add_row(
            item["name"],
            item["type"],
            size,
            str(item["modified"])
        )

    console.print(table)
    console.print(f"\nTotal Files: {result['total_files']}")
    console.print(f"Total Directories: {result['total_dirs']}")

def display_file_contents(result):
    """Display file contents."""
    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return

    console.print(Panel(
        result["content"],
        title=f"File: {result['path']}",
        subtitle=f"Size: {result['size']:,} bytes | Type: {result['type']} | Hash: {result['hash']}"
    ))

def display_search_results(result):
    """Display search results in a table."""
    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return

    table = Table(title=f"Search Results for '{result['pattern']}' in {result['directory']}")
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="blue")
    table.add_column("Size", style="yellow")
    table.add_column("Type", style="green")
    table.add_column("Modified", style="magenta")

    for match in result["matches"]:
        table.add_row(
            match["name"],
            match["path"],
            f"{match['size']:,} bytes",
            match["type"],
            str(match["modified"])
        )

    console.print(table)
    console.print(f"\nTotal Matches: {result['total_matches']}")
    console.print(f"Recursive Search: {'Yes' if result['recursive'] else 'No'}")

def display_compression_results(result):
    """Display compression results."""
    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return

    console.print(Panel(
        f"Original Size: {result['original_size']:,} bytes\n"
        f"Compressed Size: {result['compressed_size']:,} bytes\n"
        f"Compression Ratio: {result['compression_ratio']:.2f}x",
        title=f"Compression Results: {result['message']}",
        subtitle=f"Original: {result['original']} | Compressed: {result['compressed']}"
    ))

def display_content_search_results(result):
    """Display content search results."""
    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return

    table = Table(title=f"Content Search Results for '{result['pattern']}' in {result['directory']}")
    table.add_column("File", style="cyan")
    table.add_column("Line", style="yellow")
    table.add_column("Content", style="green")
    table.add_column("Context", style="blue")

    for match in result["matches"]:
        context = "\n".join(match["context"])
        table.add_row(
            match["file"],
            str(match["line"]),
            match["content"],
            context
        )

    console.print(table)
    console.print(f"\nTotal Matches: {result['total_matches']}")
    console.print(f"Max Results: {result['max_results']}")
    console.print(f"Case Sensitive: {'Yes' if result['case_sensitive'] else 'No'}")
    console.print(f"Recursive Search: {'Yes' if result['recursive'] else 'No'}")

def display_file_comparison(result):
    """Display file comparison results."""
    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return

    console.print(Panel(
        f"File 1: {result['file1']}\n"
        f"Size: {result['file1_size']:,} bytes\n"
        f"Hash: {result['file1_hash']}\n\n"
        f"File 2: {result['file2']}\n"
        f"Size: {result['file2_size']:,} bytes\n"
        f"Hash: {result['file2_hash']}\n\n"
        f"Total Differences: {result['total_differences']}",
        title="File Comparison Results"
    ))

    for diff in result["differences"]:
        console.print("\n[bold]Difference Block:[/bold]")
        for line_num, line in diff:
            if line.startswith('+'):
                console.print(f"[green]{line_num}: {line}[/green]")
            elif line.startswith('-'):
                console.print(f"[red]{line_num}: {line}[/red]")
            elif line.startswith('?'):
                console.print(f"[yellow]{line_num}: {line}[/yellow]")

def display_binary_comparison(result):
    """Display binary file comparison results."""
    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return

    console.print(Panel(
        f"File 1: {result['file1']}\n"
        f"Size: {result['file1_size']:,} bytes\n"
        f"Hash: {result['file1_hash']}\n\n"
        f"File 2: {result['file2']}\n"
        f"Size: {result['file2_size']:,} bytes\n"
        f"Hash: {result['file2_hash']}\n\n"
        f"Total Differences: {result['total_differences']}",
        title="Binary File Comparison Results"
    ))

    if result["differences"]:
        table = Table(title="Binary Differences")
        table.add_column("Offset", style="cyan")
        table.add_column("File 1", style="red")
        table.add_column("File 2", style="green")
        table.add_column("ASCII 1", style="yellow")
        table.add_column("ASCII 2", style="yellow")

        for diff in result["differences"]:
            table.add_row(
                str(diff["offset"]),
                diff["file1_byte"],
                diff["file2_byte"],
                diff["file1_ascii"],
                diff["file2_ascii"]
            )

        console.print(table)

def display_merge_results(result):
    """Display file merge results."""
    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return

    console.print(Panel(
        f"Strategy: {result['strategy']}\n"
        f"File 1 Lines: {result['file1_lines']}\n"
        f"File 2 Lines: {result['file2_lines']}\n"
        f"Merged Lines: {result['merged_lines']}\n\n"
        f"Output File: {result['output']}",
        title=f"Merge Results: {result['message']}"
    ))

def display_advanced_search_results(result):
    """Display advanced content search results."""
    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return

    table = Table(title=f"Advanced Search Results for '{result['pattern']}' in {result['directory']}")

    if result["binary_search"]:
        table.add_column("File", style="cyan")
        table.add_column("Offset", style="yellow")
        table.add_column("Content (Hex)", style="green")
        table.add_column("Context (Hex)", style="blue")

        for match in result["matches"]:
            table.add_row(
                match["file"],
                str(match["offset"]),
                match["content"],
                match["context"]
            )
    else:
        table.add_column("File", style="cyan")
        table.add_column("Line", style="yellow")
        table.add_column("Content", style="green")
        table.add_column("Context", style="blue")

        for match in result["matches"]:
            context = "\n".join(match["context"])
            table.add_row(
                match["file"],
                str(match["line"]),
                match["content"],
                context
            )

    console.print(table)
    console.print(f"\nTotal Matches: {result['total_matches']}")
    console.print(f"Max Results: {result['max_results']}")
    console.print(f"Case Sensitive: {'Yes' if result['case_sensitive'] else 'No'}")
    console.print(f"Whole Word: {'Yes' if result['whole_word'] else 'No'}")
    console.print(f"Binary Search: {'Yes' if result['binary_search'] else 'No'}")
    console.print(f"File Types: {', '.join(result['file_types']) if result['file_types'] else 'All'}")
    console.print(f"Recursive Search: {'Yes' if result['recursive'] else 'No'}")

def display_sync_results(result):
    """Display directory synchronization results."""
    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return

    console.print(Panel(
        f"Source: {result['source']}\n"
        f"Target: {result['target']}\n\n"
        f"Files Copied: {result['stats']['copied']}\n"
        f"Files Updated: {result['stats']['updated']}\n"
        f"Files Deleted: {result['stats']['deleted']}\n"
        f"Files Skipped: {result['stats']['skipped']}\n"
        f"Errors: {result['stats']['errors']}",
        title=f"Synchronization Results: {result['message']}"
    ))

def display_backup_results(result):
    """Display backup results."""
    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return

    console.print(Panel(
        f"Source: {result['source']}\n"
        f"Backup: {result['backup']}\n"
        f"Type: {result['type']}\n"
        f"Compressed: {'Yes' if result['compressed'] else 'No'}\n"
        f"Size: {result['size']:,} bytes\n"
        f"Timestamp: {result['timestamp']}",
        title=f"Backup Results: {result['message']}"
    ))

def display_encryption_results(result):
    """Display file encryption results."""
    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return

    console.print(Panel(
        f"Original: {result['original']}\n"
        f"Encrypted: {result['encrypted']}\n"
        f"Original Size: {result['original_size']:,} bytes\n"
        f"Encrypted Size: {result['encrypted_size']:,} bytes\n"
        f"Algorithm: {result['algorithm']}\n"
        f"Key Derivation: {result['key_derivation']}",
        title=f"Encryption Results: {result['message']}"
    ))

def display_decryption_results(result):
    """Display file decryption results."""
    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return

    console.print(Panel(
        f"Encrypted: {result['encrypted']}\n"
        f"Decrypted: {result['decrypted']}\n"
        f"Encrypted Size: {result['encrypted_size']:,} bytes\n"
        f"Decrypted Size: {result['decrypted_size']:,} bytes",
        title=f"Decryption Results: {result['message']}"
    ))

def display_integrity_results(result):
    """Display file integrity verification results."""
    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return

    console.print(Panel(
        f"File: {result['file']}\n"
        f"Size: {result['size']:,} bytes\n"
        f"Hash Type: {result['hash_type']}\n"
        f"Hash: {result['hash']}\n"
        f"Expected Hash: {result['expected_hash'] or 'Not provided'}\n"
        f"Status: {result['message']}",
        title="File Integrity Results"
    ))

def display_archive_results(result):
    """Display archive creation results."""
    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return

    console.print(Panel(
        f"Source: {result['source']}\n"
        f"Archive: {result['archive']}\n"
        f"Format: {result['format']}\n"
        f"Compression: {result['compression']}\n"
        f"Size: {result['size']:,} bytes",
        title=f"Archive Results: {result['message']}"
    ))

def display_extract_results(result):
    """Display archive extraction results."""
    if "error" in result:
        console.print(f"[red]Error: {result['error']}[/red]")
        return

    console.print(Panel(
        f"Archive: {result['archive']}\n"
        f"Extract Path: {result['extract_path']}\n"
        f"Extracted Files: {result['extracted_files']}",
        title=f"Extraction Results: {result['message']}"
    ))

def main():
    # Initialize file operations tool
    file_tool = FileOperationsTool()

    while True:
        display_menu()
        choice = Prompt.ask("Select an option", choices=[str(i) for i in range(1, 23)])

        if choice == "1":
            # List directory contents
            dir_path = Prompt.ask("Enter directory path", default=".")
            result = file_tool.list_directory(dir_path)
            display_directory_contents(result)

        elif choice == "2":
            # Read file
            file_path = Prompt.ask("Enter file path")
            result = file_tool.read_file(file_path)
            display_file_contents(result)

        elif choice == "3":
            # Write file
            file_path = Prompt.ask("Enter file path")
            content = Prompt.ask("Enter file content")
            overwrite = Confirm.ask("Overwrite if exists?")
            result = file_tool.write_file(file_path, content, overwrite)

            if "error" in result:
                console.print(f"[red]Error: {result['error']}[/red]")
            else:
                console.print(f"[green]File written successfully: {result['path']}[/green]")
                console.print(f"Size: {result['size']:,} bytes")
                console.print(f"Type: {result['type']}")
                console.print(f"Hash: {result['hash']}")

        elif choice == "4":
            # Delete file
            file_path = Prompt.ask("Enter file path")
            if Confirm.ask(f"Are you sure you want to delete {file_path}?"):
                result = file_tool.delete_file(file_path)
                if "error" in result:
                    console.print(f"[red]Error: {result['error']}[/red]")
                else:
                    console.print(f"[green]{result['message']}[/green]")

        elif choice == "5":
            # Copy file
            source_path = Prompt.ask("Enter source file path")
            dest_path = Prompt.ask("Enter destination file path")
            overwrite = Confirm.ask("Overwrite if exists?")
            result = file_tool.copy_file(source_path, dest_path, overwrite)

            if "error" in result:
                console.print(f"[red]Error: {result['error']}[/red]")
            else:
                console.print(f"[green]{result['message']}[/green]")
                console.print(f"Size: {result['size']:,} bytes")
                console.print(f"Type: {result['type']}")
                console.print(f"Hash: {result['hash']}")

        elif choice == "6":
            # Move file
            source_path = Prompt.ask("Enter source file path")
            dest_path = Prompt.ask("Enter destination file path")
            overwrite = Confirm.ask("Overwrite if exists?")
            result = file_tool.move_file(source_path, dest_path, overwrite)

            if "error" in result:
                console.print(f"[red]Error: {result['error']}[/red]")
            else:
                console.print(f"[green]{result['message']}[/green]")
                console.print(f"Size: {result['size']:,} bytes")
                console.print(f"Type: {result['type']}")
                console.print(f"Hash: {result['hash']}")

        elif choice == "7":
            # Search files
            pattern = Prompt.ask("Enter search pattern (e.g., *.txt)")
            dir_path = Prompt.ask("Enter directory path", default=".")
            recursive = Confirm.ask("Search recursively?")
            result = file_tool.search_files(pattern, dir_path, recursive)
            display_search_results(result)

        elif choice == "8":
            # Compress file
            file_path = Prompt.ask("Enter file path")
            format = Prompt.ask("Enter compression format", choices=['zip', 'gz', 'bz2', 'xz'], default='zip')
            delete_original = Confirm.ask("Delete original file after compression?")
            result = file_tool.compress_file(file_path, format, delete_original)
            display_compression_results(result)

        elif choice == "9":
            # Search content
            pattern = Prompt.ask("Enter search pattern (regex)")
            dir_path = Prompt.ask("Enter directory path", default=".")
            recursive = Confirm.ask("Search recursively?")
            case_sensitive = Confirm.ask("Case sensitive search?")
            max_results = int(Prompt.ask("Maximum results", default="100"))
            result = file_tool.search_content(pattern, dir_path, recursive, case_sensitive, max_results)
            display_content_search_results(result)

        elif choice == "10":
            # Compare files
            file1_path = Prompt.ask("Enter first file path")
            file2_path = Prompt.ask("Enter second file path")
            context_lines = int(Prompt.ask("Number of context lines", default="3"))
            result = file_tool.compare_files(file1_path, file2_path, context_lines)
            display_file_comparison(result)

        elif choice == "11":
            # Compare binary files
            file1_path = Prompt.ask("Enter first file path")
            file2_path = Prompt.ask("Enter second file path")
            chunk_size = int(Prompt.ask("Chunk size (bytes)", default="1024"))
            result = file_tool.compare_binary_files(file1_path, file2_path, chunk_size)
            display_binary_comparison(result)

        elif choice == "12":
            # Merge files
            file1_path = Prompt.ask("Enter first file path")
            file2_path = Prompt.ask("Enter second file path")
            output_path = Prompt.ask("Enter output file path")
            strategy = Prompt.ask("Merge strategy", choices=['interleave', 'append', 'prepend'], default='interleave')
            separator = Prompt.ask("Line separator", default="\n")
            result = file_tool.merge_files(file1_path, file2_path, output_path, strategy, separator)
            display_merge_results(result)

        elif choice == "13":
            # Advanced content search
            pattern = Prompt.ask("Enter search pattern (regex)")
            dir_path = Prompt.ask("Enter directory path", default=".")
            recursive = Confirm.ask("Search recursively?")
            case_sensitive = Confirm.ask("Case sensitive search?")
            whole_word = Confirm.ask("Whole word match?")
            binary_search = Confirm.ask("Binary search?")
            max_results = int(Prompt.ask("Maximum results", default="100"))
            context_lines = int(Prompt.ask("Context lines", default="3"))

            file_types = None
            if not binary_search:
                file_types_input = Prompt.ask("File types (comma-separated, leave empty for all)")
                if file_types_input:
                    file_types = [ft.strip() for ft in file_types_input.split(',')]

            result = file_tool.search_content_advanced(
                pattern, dir_path, recursive, case_sensitive,
                whole_word, file_types, max_results, context_lines,
                binary_search
            )
            display_advanced_search_results(result)

        elif choice == "14":
            # Synchronize directories
            source_dir = Prompt.ask("Enter source directory path")
            target_dir = Prompt.ask("Enter target directory path")
            sync_type = Prompt.ask("Sync type", choices=['mirror'], default='mirror')
            exclude_input = Prompt.ask("Exclude patterns (comma-separated, leave empty for none)")
            exclude_patterns = [p.strip() for p in exclude_input.split(',')] if exclude_input else None

            result = file_tool.sync_directories(source_dir, target_dir, sync_type, exclude_patterns)
            display_sync_results(result)

        elif choice == "15":
            # Monitor directory
            dir_path = Prompt.ask("Enter directory path to monitor")
            event_types_input = Prompt.ask("Event types to monitor (comma-separated, leave empty for all)")
            event_types = [t.strip() for t in event_types_input.split(',')] if event_types_input else None
            exclude_input = Prompt.ask("Exclude patterns (comma-separated, leave empty for none)")
            exclude_patterns = [p.strip() for p in exclude_input.split(',')] if exclude_input else None

            def event_callback(event_info):
                console.print(f"[cyan]Event: {event_info['type']}[/cyan]")
                console.print(f"[yellow]Path: {event_info['path']}[/yellow]")
                console.print(f"[green]Time: {event_info['time']}[/green]")
                console.print()

            result = file_tool.monitor_directory(dir_path, event_types, exclude_patterns, event_callback)

            if "error" in result:
                console.print(f"[red]Error: {result['error']}[/red]")
            else:
                console.print(f"[green]{result['message']}[/green]")
                console.print("Press Ctrl+C to stop monitoring...")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    result["observer"].stop()
                    result["observer"].join()
                    console.print("[yellow]Monitoring stopped[/yellow]")

        elif choice == "16":
            # Create backup
            source_path = Prompt.ask("Enter source path (file or directory)")
            backup_dir = Prompt.ask("Enter backup directory", default="backups")
            backup_type = Prompt.ask("Backup type", choices=['full'], default='full')
            compression = Confirm.ask("Compress backup?")
            max_backups = int(Prompt.ask("Maximum number of backups to keep", default="5"))

            result = file_tool.create_backup(source_path, backup_dir, backup_type, compression, max_backups)
            display_backup_results(result)

        elif choice == "17":
            # Encrypt file
            file_path = Prompt.ask("Enter file path")
            password = Prompt.ask("Enter encryption password", password=True)
            output_path = Prompt.ask("Enter output path (leave empty for default)")
            delete_original = Confirm.ask("Delete original file after encryption?")

            result = file_tool.encrypt_file(file_path, password, output_path, delete_original)
            display_encryption_results(result)

        elif choice == "18":
            # Decrypt file
            file_path = Prompt.ask("Enter encrypted file path")
            password = Prompt.ask("Enter decryption password", password=True)
            output_path = Prompt.ask("Enter output path (leave empty for default)")
            delete_encrypted = Confirm.ask("Delete encrypted file after decryption?")

            result = file_tool.decrypt_file(file_path, password, output_path, delete_encrypted)
            display_decryption_results(result)

        elif choice == "19":
            # Verify file integrity
            file_path = Prompt.ask("Enter file path")
            hash_type = Prompt.ask("Hash type", choices=['sha256', 'sha512', 'md5'], default='sha256')
            expected_hash = Prompt.ask("Expected hash (leave empty to calculate only)")

            result = file_tool.verify_file_integrity(file_path, hash_type, expected_hash)
            display_integrity_results(result)

        elif choice == "20":
            # Create archive
            source_path = Prompt.ask("Enter source path (file or directory)")
            archive_path = Prompt.ask("Enter archive path (leave empty for default)")
            format = Prompt.ask("Archive format", choices=['zip', 'tar'], default='zip')
            compression = Prompt.ask("Compression method",
                                   choices=['deflate', 'bzip2', 'lzma', 'gzip'] if format == 'zip' else ['gzip', 'bzip2', 'lzma'],
                                   default='deflate' if format == 'zip' else 'gzip')
            exclude_input = Prompt.ask("Exclude patterns (comma-separated, leave empty for none)")
            exclude_patterns = [p.strip() for p in exclude_input.split(',')] if exclude_input else None

            result = file_tool.create_archive(source_path, archive_path, format, compression, exclude_patterns)
            display_archive_results(result)

        elif choice == "21":
            # Extract archive
            archive_path = Prompt.ask("Enter archive path")
            extract_path = Prompt.ask("Enter extract path (leave empty for default)")
            password = Prompt.ask("Archive password (leave empty if none)", password=True)

            result = file_tool.extract_archive(archive_path, extract_path, password)
            display_extract_results(result)

        elif choice == "22":
            console.print("[yellow]Goodbye![/yellow]")
            break

        console.print()  # Add a blank line for better readability

if __name__ == "__main__":
    main()
