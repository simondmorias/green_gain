/**
 * Debounce utility for delaying function execution
 */

export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout | null = null;

  return function (this: unknown, ...args: Parameters<T>) {
    // eslint-disable-next-line @typescript-eslint/no-this-alias
    const context = this;

    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    timeoutId = setTimeout(() => {
      func.apply(context, args);
      timeoutId = null;
    }, delay);
  };
}

/**
 * Debounce with immediate execution option
 */
export function debounceWithImmediate<T extends (...args: unknown[]) => unknown>(
  func: T,
  delay: number,
  immediate = false
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout | null = null;

  return function (this: unknown, ...args: Parameters<T>) {
    // eslint-disable-next-line @typescript-eslint/no-this-alias
    const context = this;
    const callNow = immediate && !timeoutId;

    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    timeoutId = setTimeout(() => {
      timeoutId = null;
      if (!immediate) {
        func.apply(context, args);
      }
    }, delay);

    if (callNow) {
      func.apply(context, args);
    }
  };
}

/**
 * Async debounce for promises
 */
export function debounceAsync<T extends (...args: unknown[]) => Promise<unknown>>(
  func: T,
  delay: number
): (...args: Parameters<T>) => Promise<ReturnType<T> | void> {
  let timeoutId: NodeJS.Timeout | null = null;
  let resolvePromise: ((value: ReturnType<T> | void) => void) | null = null;

  return function (this: unknown, ...args: Parameters<T>): Promise<ReturnType<T> | void> {
    // eslint-disable-next-line @typescript-eslint/no-this-alias
    const context = this;

    return new Promise<ReturnType<T> | void>((resolve) => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      if (resolvePromise) {
        resolvePromise(undefined);
      }

      resolvePromise = resolve;

      timeoutId = setTimeout(async () => {
        try {
          const result = await func.apply(context, args);
          resolve(result as ReturnType<T>);
        } catch (error) {
          resolve(undefined);
        } finally {
          timeoutId = null;
          resolvePromise = null;
        }
      }, delay);
    });
  };
}