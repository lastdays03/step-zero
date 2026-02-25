"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export interface CheckboxProps
    extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "checked" | "onChange" | "type"> {
    checked?: boolean | "indeterminate"
    onCheckedChange?: (checked: boolean) => void
}

const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
    ({ className, checked, onCheckedChange, ...props }, ref) => {
        const innerRef = React.useRef<HTMLInputElement | null>(null)

        React.useEffect(() => {
            if (innerRef.current) {
                innerRef.current.indeterminate = checked === "indeterminate"
            }
        }, [checked])

        return (
            <input
                type="checkbox"
                className={cn(
                    "peer h-4 w-4 shrink-0 rounded-sm border border-slate-300 ring-offset-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 checked:bg-blue-600 checked:border-transparent accent-blue-600",
                    className
                )}
                ref={(node) => {
                    innerRef.current = node
                    if (typeof ref === "function") {
                        ref(node)
                    } else if (ref) {
                        ref.current = node
                    }
                }}
                checked={checked === true}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    onCheckedChange?.(e.target.checked)
                }
                {...props}
            />
        )
    }
)
Checkbox.displayName = "Checkbox"

export { Checkbox }
