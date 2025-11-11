# Temporary fix - replace lines 887-925 in derivation_builder.py
        # If we didn't find it in AST structure, try to extract from after_str_2
        # This can happen if the structure was modified but the string still contains "∧1"
        if not found_in_ast and "∧1" in after_str_2:
            import re
            # Find expressions containing "∧1" in after_str_2
            # Pattern: find parenthesized expressions like (A∧¬B∧1) or (A∧1∧B)
            pattern = r'\([^()]*∧1[^()]*\)'
            matches = re.findall(pattern, after_str_2)
            if matches:
                # Use the first match that contains "∧1"
                # Parse it to get the structure
                match_str = matches[0]
                try:
                    # Remove outer parentheses and parse
                    inner = match_str[1:-1]  # Remove ( and )
                    parsed_ast = generate_ast(inner)
                    # Normalize to boolean form
                    parsed_ast_bool = _to_bool_norm(parsed_ast)
                    # Check if it's an AND node
                    if isinstance(parsed_ast_bool, dict) and parsed_ast_bool.get("op") == "AND":
                        before_subexpr_3 = parsed_ast_bool
                        # Compute after_subexpr by removing CONST(1)
                        args = parsed_ast_bool.get("args", [])
                        new_args = [arg for arg in args if not (isinstance(arg, dict) and arg.get("op") == "CONST" and arg.get("value") == 1)]
                        if len(new_args) == 1:
                            after_subexpr_3 = new_args[0]
                        else:
                            after_subexpr_3 = {"op": "AND", "args": new_args} if new_args else None
                        # Find path in working_ast for highlighting (approximate)
                        neutral_path = None
                        for path, sub in iter_nodes(working_ast):
                            if isinstance(sub, dict) and sub.get("op") == "AND":
                                sub_args = sub.get("args", [])
                                # Check if this AND matches our after_subexpr (without CONST(1))
                                if after_subexpr_3:
                                    if canonical_str(sub) == canonical_str(after_subexpr_3):
                                        neutral_path = path
                    break
                except Exception:
                    # If parsing fails, continue with original logic
                    pass


