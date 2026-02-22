import type { ButtonDesignTokens } from '@primeuix/themes/types/button';
import type { ButtonPassThroughOptions, ButtonProps } from 'primevue/button';
import type { RendererElement, RendererNode, VNode } from 'vue';

export const buttonConfig = (): ButtonDesignTokens => {
  return {
    root: {
      paddingX: '2rem',
      paddingY: '1.2rem',
      sm: { paddingX: '.9rem', paddingY: '.9rem' },
      lg: { paddingX: '1.6rem', paddingY: '2rem' },
      label: { fontWeight: 'unset' },

      primary: {
        background: 'var(--primary-500)',
        hoverBackground: 'var(--primary-400)',
        activeBackground: 'var(--primary-600)',
        // color: 'var(--primary-surface-color)',
        // hoverColor: 'var(--primary-surface-color)',
        // activeColor: 'var(--primary-surface-color)',
      },

      secondary: {
        color: 'var(--text-color)',
        hoverColor: 'var(--text-color)',
        activeColor: 'var(--text-color)',
        background: 'var(--secondary-600)',
        hoverBackground: 'var(--secondary-700)',
        activeBackground: 'var(--secondary-700)',
        borderColor: 'transparent',
        hoverBorderColor: 'transparent',
        activeBorderColor: 'transparent',
      },
    },
    outlined: {
      secondary: {
        borderColor: 'var(--secondary-800)',
        color: 'var(--secondary-800)',
      }
    },
  };
};

export const buttonPt = (instance: VNode<RendererNode, RendererElement, ButtonProps>): ButtonPassThroughOptions => {
  return {
    root: {
      class: !instance.props?.size ? 'font-14-b' : instance.props.size === 'small' ? 'font-12-r' : 'font-18-b',
    },

    icon: {
      ...((instance.props?.icon && instance.props?.icon.includes('<svg')) && {
        innerHTML: instance.props?.icon,
        classList: `p-button-icon-svg p-button-icon-${instance.props?.iconPos || 'left'} ${instance.props?.iconClass || ''}`,
        // @ts-expect-error next-line
        style: { color: instance.attrs['icon-color'] || 'currentColor' },
      }),
      ...((instance.props?.icon && !instance.props?.icon.includes('<svg')) && { class: instance.props?.icon }),
    },
  };
};
