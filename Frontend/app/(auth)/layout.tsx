import React from 'react';

/**
 * AuthLayout Component
 * 
 * This component is a layout wrapper for authentication-related pages (like login, signup, etc.).
 * It centers its children (typically forms or auth-related content) both horizontally and vertically.
 * 
 * Props:
 * - children: React.ReactNode - The content to be displayed within the layout.
 */
const AuthLayout = ({
    children
}: {
    children: React.ReactNode;
}) => {
    return (
        // Outer container with full viewport height, flex display, and center alignment
        <div className="flex items-center justify-center min-h-screen bg-gray-100">
            {/* Inner container for additional styling, if needed */}
            <div className="w-full max-w-xs px-4 py-8">
                {children}
            </div>
        </div>
    );
}

export default AuthLayout;
