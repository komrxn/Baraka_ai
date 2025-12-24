import type { ToggleButtonDesignTokens } from '@primeuix/themes/types/togglebutton';
import type { ToggleButtonPassThroughOptions, ToggleButtonProps } from 'primevue';
import type { RendererElement, RendererNode, VNode } from 'vue';

export const toggleButtonConfig = (): ToggleButtonDesignTokens => {
  return {
    root: {
      padding: '.4rem',
      sm: { padding: '.3rem' },
      lg: { padding: '.5rem' },
    },
    content: {
      borderRadius: '.5rem',
      padding: '0.7rem 1.2rem',
      sm: { padding: '0.4rem 1.2rem' },
      lg: { padding: '1rem 1.4rem' },
    },

    colorScheme: {
      light: {
        root: {
          color: '{surface.950}',
          hoverColor: '{surface.950}',
          checkedColor: '{formField.color}',

          background: '{formField.background}',
          borderColor: '{formField.borderColor}',
          hoverBackground: '{formField.background}',
          checkedBackground: '{formField.background}',
        },
        content: {
          checkedBackground: '{surface.100}',
        },
      },
      dark: {
        root: {
          color: '{surface.400}',
          hoverColor: '{surface.100}',
          checkedColor: '{formField.color}',


          background: 'var(--secondary-500)',
          // borderColor: '{formField.borderColor}',
          checkedBorderColor: '{formField.borderColor}',
          hoverBackground: 'var(--card-hover)',
          checkedBackground: 'var(--card-accent)',
        },
        content: {
          checkedBackground: '{surface.600}',
        },
      },
    },
  };
};

export const toggleButtonPt = (instance?: VNode<RendererNode, RendererElement, ToggleButtonProps>): ToggleButtonPassThroughOptions => {
  return {
    root: {
      class: (!instance || !instance.props?.size) ? 'font-14-b' : instance.props.size === 'small' ? 'font-12-r' : 'font-18-b',
    },
  };
};
