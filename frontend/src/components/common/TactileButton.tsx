import React from 'react';

interface TactileButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ElementType;
  children: React.ReactNode;
}

export const TactileButton: React.FC<TactileButtonProps> = ({
  variant = 'primary',
  size = 'md',
  icon: Icon,
  children,
  className = '',
  disabled,
  ...props
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'secondary':
        return 'bg-[#141222] text-[#D1CFDC] border border-white/[0.08] shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] hover:bg-[#1A182C] hover:text-white';
      case 'ghost':
        return 'bg-transparent text-text-secondary hover:text-white hover:bg-white/[0.05] border border-transparent';
      case 'primary':
      default:
        return 'bg-gradient-to-b from-violet-500 to-indigo-600 text-white border border-violet-400/40 shadow-[inset_0_1px_0_rgba(255,255,255,0.3),0_4px_16px_rgba(124,58,237,0.35)] hover:from-violet-400 hover:to-indigo-500';
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'sm':
        return 'px-2.5 py-1 text-xs rounded-lg gap-1.5';
      case 'lg':
        return 'px-5 py-2.5 text-sm rounded-xl gap-2.5';
      case 'md':
      default:
        return 'px-3.5 py-1.5 text-xs rounded-xl gap-2';
    }
  };

  return (
    <button
      disabled={disabled}
      className={`inline-flex items-center justify-center font-semibold transition-all duration-150 select-none cursor-pointer active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none ${getVariantStyles()} ${getSizeStyles()} ${className}`}
      {...props}
    >
      {Icon && <Icon className="w-3.5 h-3.5 flex-shrink-0" />}
      <span>{children}</span>
    </button>
  );
};
